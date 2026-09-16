"""
Half-Duplex Audio Streamer for FT-991A and OpenAI Realtime S2S.
Captures USB Audio CODEC input, resamples to 24kHz PCM16, and plays back response audio.
Computes real-time VU levels for telemetry.
"""

import math
import time
import queue
import threading
import logging
import numpy as np
from scipy import signal
from typing import Optional, Callable, Dict, Any

from backend.audio.devices import resolve_device_index
from backend.audio.vad import calculate_audio_levels
from backend.config import config_manager

logger = logging.getLogger("audio_streamer")

OPENAI_SAMPLE_RATE = 24000  # 24kHz standard for OpenAI Realtime PCM16


def resample_pcm16(
    pcm_bytes: bytes,
    from_rate: int,
    to_rate: int,
    from_channels: int = 1,
    to_channels: int = 1
) -> bytes:
    """Resample 16-bit PCM bytes between sample rates and channel counts."""
    if not pcm_bytes or from_rate == to_rate and from_channels == to_channels:
        return pcm_bytes

    try:
        audio_data = np.frombuffer(pcm_bytes, dtype=np.int16)
        if from_channels > 1:
            audio_data = audio_data.reshape(-1, from_channels)
            # Mixdown to mono if needed
            if to_channels == 1:
                audio_data = np.mean(audio_data, axis=1).astype(np.int16)

        if from_rate != to_rate:
            # Use polyphase rational resampling for low latency & high fidelity
            gcd = math.gcd(from_rate, to_rate)
            up = to_rate // gcd
            down = from_rate // gcd
            resampled = signal.resample_poly(audio_data.astype(np.float32), up, down)
            audio_data = np.clip(resampled, -32768, 32767).astype(np.int16)

        return audio_data.tobytes()
    except Exception as e:
        logger.error(f"Resampling error ({from_rate}->{to_rate}): {e}")
        return pcm_bytes


class AudioStreamer:
    def __init__(self):
        self.input_stream = None
        self.output_stream = None
        self.sd = None
        self._init_sounddevice()

        # State flags
        self.is_capturing = False
        self.is_playing = False

        # Live telemetry VU metrics (0-100%)
        self.rx_rms = 0.0
        self.rx_peak = 0.0
        self.tx_rms = 0.0
        self.tx_peak = 0.0

        # Callbacks
        self.on_rx_chunk: Optional[Callable[[bytes], None]] = None

        # Playback buffer queue
        self.tx_queue: queue.Queue = queue.Queue()
        self.playback_thread: Optional[threading.Thread] = None
        self._stop_playback_event = threading.Event()

        # Hardware params
        self.hw_input_rate = 48000
        self.hw_output_rate = 48000

    def _init_sounddevice(self):
        try:
            import sounddevice as sd
            self.sd = sd
        except Exception as e:
            logger.warning(f"Could not load sounddevice module: {e}")
            self.sd = None

    def start(self, on_rx_chunk: Callable[[bytes], None]):
        """Initialize and open input and output audio devices."""
        self.on_rx_chunk = on_rx_chunk
        cfg = config_manager.get()

        if cfg.simulated_mode or not self.sd:
            logger.info("AudioStreamer running in virtual/simulated mode.")
            self._start_simulated_audio()
            return

        in_dev = resolve_device_index(cfg.audio_input_device, is_input=True)
        out_dev = resolve_device_index(cfg.audio_output_device, is_input=False)

        try:
            # Query hardware rates
            if in_dev is not None:
                dev_info = self.sd.query_devices(in_dev)
                self.hw_input_rate = int(dev_info.get("default_samplerate", 48000))
            if out_dev is not None:
                dev_info = self.sd.query_devices(out_dev)
                self.hw_output_rate = int(dev_info.get("default_samplerate", 48000))

            logger.info(
                f"Opening Audio Streams: IN[id={in_dev}, rate={self.hw_input_rate}], OUT[id={out_dev}, rate={self.hw_output_rate}]"
            )

            # Open input audio stream (half-duplex RX)
            self.input_stream = self.sd.InputStream(
                device=in_dev,
                channels=1,
                samplerate=self.hw_input_rate,
                dtype="int16",
                blocksize=int(self.hw_input_rate * 0.05),  # 50ms blocks
                callback=self._input_callback,
            )
            self.input_stream.start()

            # Open output audio stream (half-duplex TX)
            self.output_stream = self.sd.OutputStream(
                device=out_dev,
                channels=1,
                samplerate=self.hw_output_rate,
                dtype="int16",
                blocksize=int(self.hw_output_rate * 0.05),  # 50ms blocks
                callback=self._output_callback,
            )
            self.output_stream.start()
            logger.info("Audio input and output streams active.")
        except Exception as e:
            logger.error(f"Failed to start hardware audio streams: {e}. Falling back to virtual audio.")
            self._start_simulated_audio()

    def _input_callback(self, indata, frames, time_info, status):
        """Called by PortAudio for every incoming mic block."""
        if status:
            logger.debug(f"Input stream status: {status}")

        raw_bytes = indata.tobytes()
        rms, peak = calculate_audio_levels(raw_bytes)
        self.rx_rms = rms
        self.rx_peak = peak

        if self.is_capturing and self.on_rx_chunk:
            # Resample to 24kHz mono PCM for OpenAI Realtime
            pcm_24k = resample_pcm16(
                pcm_bytes=raw_bytes,
                from_rate=self.hw_input_rate,
                to_rate=OPENAI_SAMPLE_RATE,
                from_channels=1,
                to_channels=1,
            )
            self.on_rx_chunk(pcm_24k)

    def _output_callback(self, outdata, frames, time_info, status):
        """Called by PortAudio when speaker needs audio data."""
        try:
            chunk = self.tx_queue.get_nowait()
            rms, peak = calculate_audio_levels(chunk)
            self.tx_rms = rms
            self.tx_peak = peak
            out_samples = np.frombuffer(chunk, dtype=np.int16)

            # Pad or truncate if chunk size differs from expected frames
            if len(out_samples) < frames:
                outdata[:len(out_samples), 0] = out_samples
                outdata[len(out_samples):, 0] = 0
            else:
                outdata[:, 0] = out_samples[:frames]
        except queue.Empty:
            outdata.fill(0)
            self.tx_rms = 0.0
            self.tx_peak = 0.0
            if self.is_playing:
                self.is_playing = False

    def enqueue_tx_audio(self, pcm24k_bytes: bytes):
        """Accepts 24kHz PCM16 audio from OpenAI and feeds the playback pipeline."""
        if not pcm24k_bytes:
            return

        self.is_playing = True
        # Resample from 24kHz to hardware output rate
        hw_pcm = resample_pcm16(
            pcm_bytes=pcm24k_bytes,
            from_rate=OPENAI_SAMPLE_RATE,
            to_rate=self.hw_output_rate,
            from_channels=1,
            to_channels=1,
        )

        # Split into blocks matching callback size (~50ms)
        block_bytes = int(self.hw_output_rate * 0.05) * 2  # 2 bytes per int16 sample
        for i in range(0, len(hw_pcm), block_bytes):
            chunk = hw_pcm[i:i + block_bytes]
            self.tx_queue.put(chunk)

    def is_playback_finished(self) -> bool:
        """Returns True if the output playback buffer has been fully drained."""
        return self.tx_queue.empty() and not self.is_playing

    def set_capturing(self, capturing: bool):
        """Control whether captured audio is fed into OpenAI."""
        self.is_capturing = capturing
        if not capturing:
            self.rx_rms = 0.0
            self.rx_peak = 0.0

    def get_vu_levels(self) -> Dict[str, float]:
        """Return instantaneous VU levels for UI."""
        return {
            "rx_rms": self.rx_rms,
            "rx_peak": self.rx_peak,
            "tx_rms": self.tx_rms,
            "tx_peak": self.tx_peak,
        }

    def _start_simulated_audio(self):
        """Simulation loop when running without physical sound hardware."""
        self.hw_input_rate = 24000
        self.hw_output_rate = 24000

        def sim_worker():
            while not self._stop_playback_event.is_set():
                if self.is_capturing:
                    # Generate simulated voice audio (random speech-like modulated noise)
                    t = np.linspace(0, 0.05, int(24000 * 0.05), endpoint=False)
                    voice = (
                        0.4 * np.sin(2 * np.pi * 300 * t) +
                        0.3 * np.sin(2 * np.pi * 800 * t) +
                        0.2 * np.random.normal(0, 0.05, len(t))
                    )
                    samples = (voice * 16000).clip(-32768, 32767).astype(np.int16)
                    pcm = samples.tobytes()
                    rms, peak = calculate_audio_levels(pcm)
                    self.rx_rms = rms
                    self.rx_peak = peak
                    if self.on_rx_chunk:
                        self.on_rx_chunk(pcm)
                else:
                    self.rx_rms = max(0.0, self.rx_rms - 5.0)
                    self.rx_peak = max(0.0, self.rx_peak - 5.0)

                # Process playback queue in simulation
                try:
                    chunk = self.tx_queue.get_nowait()
                    rms, peak = calculate_audio_levels(chunk)
                    self.tx_rms = rms
                    self.tx_peak = peak
                    self.is_playing = True
                except queue.Empty:
                    self.tx_rms = 0.0
                    self.tx_peak = 0.0
                    self.is_playing = False

                time.sleep(0.05)

        self.playback_thread = threading.Thread(target=sim_worker, daemon=True)
        self.playback_thread.start()

    def stop(self):
        """Stop and cleanup audio streams."""
        self._stop_playback_event.set()
        try:
            if self.input_stream:
                self.input_stream.stop()
                self.input_stream.close()
            if self.output_stream:
                self.output_stream.stop()
                self.output_stream.close()
        except Exception as e:
            logger.debug(f"Error during audio stream cleanup: {e}")
