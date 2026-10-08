"""
Pipecat Radio Audio Transport for Yaesu FT-991A.
Implements BaseTransport, BaseInputTransport, and BaseOutputTransport to stream
half-duplex amateur radio audio, gate squelch, and manage hardware PTT with relay settling delays.
"""

import time
import queue
import asyncio
import logging
import threading
import numpy as np
from typing import Optional, Callable, Dict, Any

from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.base_input import BaseInputTransport
from pipecat.transports.base_output import BaseOutputTransport
from pipecat.frames.frames import (
    AudioRawFrame,
    UserStartedSpeakingFrame,
    UserStoppedSpeakingFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    Frame,
)
from pipecat.processors.frame_processor import FrameDirection

from backend.config import config_manager
from backend.audio.streamer import resample_pcm16
from backend.audio.vad import calculate_audio_levels
from backend.cat.base import BaseRadio

logger = logging.getLogger("radio_transport")


class RadioInputTransport(BaseInputTransport):
    """Captures audio from transceiver soundcard and emits AudioRawFrames when squelch opens."""

    def __init__(
        self,
        radio: BaseRadio,
        sample_rate: int = 16000,
        params: Optional[TransportParams] = None,
        **kwargs
    ):
        if params is None:
            params = TransportParams(audio_in_enabled=True, audio_out_enabled=False)
        super().__init__(params=params, **kwargs)

        self.radio = radio
        self.target_sample_rate = sample_rate
        self.is_transmitting = False
        self.signal_active = False
        self.rx_start_time = 0.0
        self.signal_drop_time = 0.0
        self.manual_override = False

        # Audio stream references
        self._input_stream = None
        self._running = False
        self.sd = None
        self._init_sounddevice()

        # Telemetry levels
        self.rx_rms = 0.0
        self.rx_peak = 0.0

        # Accumulated audio for current transmission
        self.rx_buffer = bytearray()
        self.on_transmission_done: Optional[Callable[[bytes, float], None]] = None

    def _init_sounddevice(self):
        try:
            import sounddevice as sd
            self.sd = sd
        except Exception as e:
            logger.warning(f"Could not load sounddevice in RadioInputTransport: {e}")

    def set_manual_ptt(self, active: bool):
        self.manual_override = active

    def start_capture(self, loop: asyncio.AbstractEventLoop):
        self._running = True
        cfg = config_manager.get()

        if cfg.simulated_mode or not self.sd:
            threading.Thread(target=self._simulated_rx_worker, args=(loop,), daemon=True).start()
            return

        try:
            from backend.audio.devices import resolve_device_index
            in_dev = resolve_device_index(cfg.audio_input_device, is_input=True)
            hw_rate = 48000
            if in_dev is not None:
                info = self.sd.query_devices(in_dev)
                hw_rate = int(info.get("default_samplerate", 48000))

            blocksize = int(hw_rate * 0.05)  # 50ms blocks

            def audio_cb(indata, frames, time_info, status):
                if not self._running:
                    return
                raw_bytes = indata.tobytes()
                # Resample to pipeline target sample rate
                pcm_target = resample_pcm16(
                    pcm_bytes=raw_bytes,
                    from_rate=hw_rate,
                    to_rate=self.target_sample_rate,
                )
                rms, peak = calculate_audio_levels(pcm_target)
                self.rx_rms = rms
                self.rx_peak = peak

                # Pass to async worker
                asyncio.run_coroutine_threadsafe(
                    self._handle_incoming_pcm(pcm_target),
                    loop
                )

            self._input_stream = self.sd.InputStream(
                device=in_dev,
                channels=1,
                samplerate=hw_rate,
                dtype="int16",
                blocksize=blocksize,
                callback=audio_cb,
            )
            self._input_stream.start()
            logger.info("RadioInputTransport audio capture stream started.")
        except Exception as e:
            logger.error(f"Failed to open hardware input stream: {e}. Falling back to simulation.")
            threading.Thread(target=self._simulated_rx_worker, args=(loop,), daemon=True).start()

    async def _handle_incoming_pcm(self, pcm_bytes: bytes):
        """Called for every incoming audio block."""
        cfg = config_manager.get()
        telemetry = self.radio.poll_telemetry()
        s_meter = telemetry.get("s_meter", 0)
        signal_present = (s_meter >= cfg.s_meter_threshold) or self.manual_override
        now = time.time()

        if signal_present:
            if not self.signal_active:
                # Squelch just broke open!
                self.signal_active = True
                self.rx_start_time = now
                self.signal_drop_time = 0.0
                self.rx_buffer.clear()
                logger.info(f"Squelch OPEN (S-Meter={s_meter}). Emitting UserStartedSpeakingFrame.")
                await self.push_frame(UserStartedSpeakingFrame(), FrameDirection.DOWNSTREAM)

            self.rx_buffer.extend(pcm_bytes)
            frame = AudioRawFrame(
                audio=pcm_bytes,
                sample_rate=self.target_sample_rate,
                num_channels=1,
            )
            await self.push_frame(frame, FrameDirection.DOWNSTREAM)
        else:
            if self.signal_active:
                if self.signal_drop_time == 0.0:
                    self.signal_drop_time = now
                elif (now - self.signal_drop_time) >= (cfg.rx_hang_time_ms / 1000.0):
                    # Squelch hang time elapsed
                    self.signal_active = False
                    duration = now - self.rx_start_time - (cfg.rx_hang_time_ms / 1000.0)
                    logger.info(f"Squelch CLOSED ({duration:.2f}s). Emitting UserStoppedSpeakingFrame.")
                    await self.push_frame(UserStoppedSpeakingFrame(), FrameDirection.DOWNSTREAM)

                    if self.on_transmission_done and (duration >= 0.3 or len(self.rx_buffer) >= 4800):
                        self.on_transmission_done(bytes(self.rx_buffer), duration)

    def _simulated_rx_worker(self, loop: asyncio.AbstractEventLoop):
        """Generates synthetic audio when simulating or without audio hardware."""
        while self._running:
            if self.manual_override:
                t = np.linspace(0, 0.05, int(self.target_sample_rate * 0.05), endpoint=False)
                voice = 0.4 * np.sin(2 * np.pi * 400 * t) + 0.2 * np.random.normal(0, 0.05, len(t))
                samples = (voice * 16000).clip(-32768, 32767).astype(np.int16)
                pcm = samples.tobytes()
                rms, peak = calculate_audio_levels(pcm)
                self.rx_rms = rms
                self.rx_peak = peak
                asyncio.run_coroutine_threadsafe(self._handle_incoming_pcm(pcm), loop)
            else:
                self.rx_rms = max(0.0, self.rx_rms - 5.0)
                self.rx_peak = max(0.0, self.rx_peak - 5.0)
            time.sleep(0.05)

    def stop(self):
        self._running = False
        if self._input_stream:
            try:
                self._input_stream.stop()
                self._input_stream.close()
            except Exception:
                pass


class RadioOutputTransport(BaseOutputTransport):
    """Receives AudioRawFrames from Pipecat pipeline, keys PTT, and streams audio to transceiver."""

    def __init__(
        self,
        radio: BaseRadio,
        sample_rate: int = 16000,
        params: Optional[TransportParams] = None,
        **kwargs
    ):
        if params is None:
            params = TransportParams(audio_in_enabled=False, audio_out_enabled=True)
        super().__init__(params=params, **kwargs)

        self.radio = radio
        self.target_sample_rate = sample_rate
        self.sd = None
        self._init_sounddevice()

        self._output_stream = None
        self._playback_queue: queue.Queue = queue.Queue()
        self._running = False
        self.is_transmitting = False

        self.tx_rms = 0.0
        self.tx_peak = 0.0
        self.tx_buffer = bytearray()
        self.on_transmission_done: Optional[Callable[[bytes, float], None]] = None

    def _init_sounddevice(self):
        try:
            import sounddevice as sd
            self.sd = sd
        except Exception:
            pass

    def start_playback_stream(self, loop: asyncio.AbstractEventLoop):
        self._running = True
        cfg = config_manager.get()

        if cfg.simulated_mode or not self.sd:
            threading.Thread(target=self._simulated_tx_worker, args=(loop,), daemon=True).start()
            return

        try:
            from backend.audio.devices import resolve_device_index
            out_dev = resolve_device_index(cfg.audio_output_device, is_input=False)
            hw_rate = 48000
            if out_dev is not None:
                info = self.sd.query_devices(out_dev)
                hw_rate = int(info.get("default_samplerate", 48000))

            blocksize = int(hw_rate * 0.05)

            def out_cb(outdata, frames, time_info, status):
                needed = frames * 2
                chunk = bytearray()
                while len(chunk) < needed:
                    try:
                        part = self._playback_queue.get_nowait()
                        chunk.extend(part)
                    except queue.Empty:
                        break

                if chunk:
                    samples = np.frombuffer(bytes(chunk), dtype=np.int16)
                    if len(samples) < frames:
                        outdata[:len(samples), 0] = samples
                        outdata[len(samples):, 0] = 0
                    else:
                        outdata[:, 0] = samples[:frames]
                    rms, peak = calculate_audio_levels(bytes(chunk))
                    self.tx_rms = rms
                    self.tx_peak = peak
                else:
                    outdata.fill(0)
                    self.tx_rms = 0.0
                    self.tx_peak = 0.0

            self._output_stream = self.sd.OutputStream(
                device=out_dev,
                channels=1,
                samplerate=hw_rate,
                dtype="int16",
                blocksize=blocksize,
                callback=out_cb,
            )
            self._output_stream.start()
            logger.info("RadioOutputTransport hardware output stream started.")
        except Exception as e:
            logger.error(f"Failed to open hardware output stream: {e}. Falling back to simulation.")
            threading.Thread(target=self._simulated_tx_worker, args=(loop,), daemon=True).start()

    def _simulated_tx_worker(self, loop: asyncio.AbstractEventLoop):
        while self._running:
            try:
                chunk = self._playback_queue.get(timeout=0.05)
                rms, peak = calculate_audio_levels(chunk)
                self.tx_rms = rms
                self.tx_peak = peak
            except queue.Empty:
                self.tx_rms = 0.0
                self.tx_peak = 0.0

    async def write_audio_frame(self, frame: AudioRawFrame):
        """Called when an AudioRawFrame arrives from TTS or Realtime model."""
        cfg = config_manager.get()
        audio_bytes = frame.audio

        if not self.is_transmitting:
            # Key PTT on first outgoing audio frame
            self.is_transmitting = True
            self.tx_buffer.clear()
            logger.info("Keying transceiver PTT for AI transmission...")
            self.radio.set_ptt(True)
            await self.push_frame(BotStartedSpeakingFrame(), FrameDirection.UPSTREAM)
            # Settle relays
            await asyncio.sleep(cfg.pre_tx_delay_ms / 1000.0)

        self.tx_buffer.extend(audio_bytes)
        self._playback_queue.put(audio_bytes)

    async def finish_turn(self):
        """Wait for audio queue to drain, apply post-TX delay, and unkey PTT."""
        if not self.is_transmitting:
            return

        cfg = config_manager.get()
        # Wait until queue drains
        while not self._playback_queue.empty():
            await asyncio.sleep(0.04)

        await asyncio.sleep(cfg.post_tx_delay_ms / 1000.0)
        logger.info("AI transmission audio finished. Releasing PTT...")
        self.radio.set_ptt(False)
        self.is_transmitting = False
        await self.push_frame(BotStoppedSpeakingFrame(), FrameDirection.UPSTREAM)

        if self.on_transmission_done and len(self.tx_buffer) > 0:
            duration = len(self.tx_buffer) / (self.target_sample_rate * 2)
            self.on_transmission_done(bytes(self.tx_buffer), duration)

    def set_ptt(self, active: bool):
        """Direct PTT keying on transceiver."""
        self.is_transmitting = active
        self.radio.set_ptt(active)

    def stop(self):
        self._running = False
        if self._output_stream:
            try:
                self._output_stream.stop()
                self._output_stream.close()
            except Exception:
                pass


class RadioAudioTransport(BaseTransport):
    """Full two-way Pipecat Transport coordinating input and output for amateur transceiver."""

    def __init__(
        self,
        radio: BaseRadio,
        sample_rate: int = 16000,
        **kwargs
    ):
        super().__init__(name="RadioAudioTransport", **kwargs)
        self._input = RadioInputTransport(radio=radio, sample_rate=sample_rate)
        self._output = RadioOutputTransport(radio=radio, sample_rate=sample_rate)

    def input(self) -> RadioInputTransport:
        return self._input

    def output(self) -> RadioOutputTransport:
        return self._output
