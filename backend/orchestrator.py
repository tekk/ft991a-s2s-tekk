"""
Half-Duplex Transceiver State Machine Orchestrator.
Coordinates Yaesu CAT S-Meter trigger, Audio Capture, OpenAI Realtime S2S,
PTT Keying, Audio Playback, Recording, and Telemetry Broadcasting.
"""

import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from fastapi import WebSocket

from backend.config import config_manager
from backend.cat.base import BaseRadio
from backend.cat.ft991a import FT991ARadio
from backend.cat.mock_radio import MockRadio
from backend.audio.streamer import AudioStreamer, OPENAI_SAMPLE_RATE
from backend.audio.devices import get_audio_devices
from backend.openai_client.realtime import OpenAIRealtimeClient
from backend.recording.recorder import audio_recorder
from backend.recording.disk_manager import disk_manager

logger = logging.getLogger("orchestrator")


class TransceiverOrchestrator:
    def __init__(self):
        self.state = "IDLE"  # IDLE, RX, PROCESSING, TX_PREPARE, TX
        self.radio: BaseRadio = FT991ARadio()
        self.streamer: AudioStreamer = AudioStreamer()
        self.openai_client: OpenAIRealtimeClient = OpenAIRealtimeClient()

        # Telemetry & WebSockets
        self.active_websockets: Set[WebSocket] = set()
        self.running = False
        self._main_task: Optional[asyncio.Task] = None
        self._telemetry_task: Optional[asyncio.Task] = None

        # State machine tracking
        self.signal_drop_time = 0.0
        self.rx_buffer = bytearray()
        self.tx_buffer = bytearray()
        self.manual_ptt_override = False

        # Live transcripts
        self.latest_user_transcript = ""
        self.latest_ai_transcript = ""
        self.transmission_log: List[Dict[str, Any]] = []

        # Setup audio and OpenAI callbacks
        self._setup_callbacks()

    def _setup_callbacks(self):
        # Audio streamer -> OpenAI
        def on_rx_audio(pcm_chunk: bytes):
            if self.state == "RX":
                self.rx_buffer.extend(pcm_chunk)
                asyncio.run_coroutine_threadsafe(
                    self.openai_client.append_input_audio(pcm_chunk),
                    self.loop
                )

        self.streamer_rx_cb = on_rx_audio

        # OpenAI -> Orchestrator
        def on_ai_audio(pcm_chunk: bytes):
            self.tx_buffer.extend(pcm_chunk)
            self.streamer.enqueue_tx_audio(pcm_chunk)
            if self.state == "PROCESSING":
                self.state = "TX_PREPARE"

        def on_ai_transcript_delta(delta: str):
            self.latest_ai_transcript += delta

        def on_ai_transcript_done(full_text: str):
            self.latest_ai_transcript = full_text

        def on_user_transcript(text: str):
            self.latest_user_transcript = text

        self.openai_client.on_audio_delta = on_ai_audio
        self.openai_client.on_assistant_transcript_delta = on_ai_transcript_delta
        self.openai_client.on_assistant_transcript_done = on_ai_transcript_done
        self.openai_client.on_user_transcript = on_user_transcript

    async def start(self):
        """Initialize radio, audio streams, OpenAI client, and background tasks."""
        self.loop = asyncio.get_running_loop()
        self.running = True
        cfg = config_manager.get()

        # Choose Radio Driver (Physical or Mock)
        if cfg.simulated_mode:
            self.radio = MockRadio()
        else:
            self.radio = FT991ARadio()

        self.radio.connect()

        # Start Audio Streams
        self.streamer.start(on_rx_chunk=self.streamer_rx_cb)

        # Connect to OpenAI Realtime
        if cfg.openai_api_key:
            await self.openai_client.connect()
        else:
            logger.warning("No OpenAI API Key set. OpenAI Realtime will connect once key is configured.")

        # Launch background loops
        self._main_task = asyncio.create_task(self._orchestration_loop())
        self._telemetry_task = asyncio.create_task(self._telemetry_broadcast_loop())
        logger.info("Transceiver Orchestrator started.")

    async def reload_radio_and_audio(self):
        """Re-initializes radio and audio when user changes device settings in Web UI."""
        cfg = config_manager.get()
        logger.info("Reloading radio CAT and audio device connections...")
        self.radio.disconnect()
        if cfg.simulated_mode:
            self.radio = MockRadio()
        else:
            self.radio = FT991ARadio()
        self.radio.connect()

        self.streamer.stop()
        self.streamer.start(on_rx_chunk=self.streamer_rx_cb)

        if cfg.openai_api_key and not self.openai_client.is_connected:
            await self.openai_client.connect()

    async def _orchestration_loop(self):
        """Main real-time state machine cycle."""
        while self.running:
            try:
                cfg = config_manager.get()
                telemetry = self.radio.poll_telemetry()
                s_meter = telemetry.get("s_meter", 0)
                threshold = cfg.s_meter_threshold
                signal_present = s_meter >= threshold

                now = time.time()

                # State: IDLE -> Watching for incoming signal
                if self.state == "IDLE":
                    if signal_present or self.manual_ptt_override:
                        logger.info(f"Signal detected! S-Meter={s_meter} (Threshold={threshold}). Starting RX...")
                        self.state = "RX"
                        self.rx_buffer.clear()
                        self.tx_buffer.clear()
                        self.latest_user_transcript = ""
                        self.latest_ai_transcript = ""
                        self.streamer.set_capturing(True)
                        self.signal_drop_time = 0.0

                # State: RX -> Receiving incoming transmission
                elif self.state == "RX":
                    if signal_present:
                        self.signal_drop_time = 0.0
                    else:
                        if self.signal_drop_time == 0.0:
                            self.signal_drop_time = now
                        elif (now - self.signal_drop_time) >= (cfg.rx_hang_time_ms / 1000.0):
                            logger.info("Signal dropped below threshold and hang-time elapsed. Finishing RX...")
                            self.state = "PROCESSING"
                            self.streamer.set_capturing(False)

                            # Save RX recording asynchronously
                            rx_data = bytes(self.rx_buffer)
                            asyncio.create_task(self._finalize_rx(rx_data))

                            # Commit and trigger AI turn
                            await self.openai_client.commit_and_generate()

                # State: TX_PREPARE -> Audio ready from AI, engage PTT and wait pre-TX relay settle
                elif self.state == "TX_PREPARE":
                    logger.info("Keying PTT for AI transmission...")
                    self.radio.set_ptt(True)
                    await asyncio.sleep(cfg.pre_tx_delay_ms / 1000.0)
                    self.state = "TX"

                # State: TX -> Transmitting AI response audio to radio
                elif self.state == "TX":
                    # Check if audio output buffer is drained
                    if self.streamer.is_playback_finished():
                        logger.info("AI audio output complete. Releasing PTT...")
                        await asyncio.sleep(cfg.post_tx_delay_ms / 1000.0)
                        self.radio.set_ptt(False)

                        # Save TX recording asynchronously
                        tx_data = bytes(self.tx_buffer)
                        asyncio.create_task(self._finalize_tx(tx_data))

                        self.state = "IDLE"

            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}", exc_info=True)

            await asyncio.sleep(0.04)  # ~25Hz polling rate

    async def _finalize_rx(self, rx_bytes: bytes):
        """Save received audio recording."""
        rec_info = await audio_recorder.save_recording(
            pcm_bytes=rx_bytes,
            sample_rate=OPENAI_SAMPLE_RATE,
            channels=1,
            prefix="rx",
        )
        if rec_info:
            log_item = {
                "id": rec_info["filename"],
                "type": "RX",
                "timestamp": time.time(),
                "duration": rec_info["duration_seconds"],
                "url": rec_info["url"],
                "transcript": self.latest_user_transcript,
            }
            self.transmission_log.insert(0, log_item)
            if len(self.transmission_log) > 50:
                self.transmission_log.pop()

    async def _finalize_tx(self, tx_bytes: bytes):
        """Save transmitted audio recording."""
        rec_info = await audio_recorder.save_recording(
            pcm_bytes=tx_bytes,
            sample_rate=OPENAI_SAMPLE_RATE,
            channels=1,
            prefix="tx",
        )
        if rec_info:
            log_item = {
                "id": rec_info["filename"],
                "type": "TX",
                "timestamp": time.time(),
                "duration": rec_info["duration_seconds"],
                "url": rec_info["url"],
                "transcript": self.latest_ai_transcript,
            }
            self.transmission_log.insert(0, log_item)
            if len(self.transmission_log) > 50:
                self.transmission_log.pop()

    def set_manual_ptt(self, active: bool):
        """Manual PTT override from Web UI."""
        self.manual_ptt_override = active
        self.radio.set_ptt(active)
        if active:
            self.state = "TX"
        else:
            if self.state == "TX":
                self.state = "IDLE"

    def trigger_simulated_rx(self, duration: float = 4.0):
        """Trigger simulated incoming signal on mock radio."""
        if isinstance(self.radio, MockRadio):
            self.radio.trigger_simulated_transmission(duration)
        else:
            # Force RX state even on physical radio for testing
            self.state = "RX"
            self.rx_buffer.clear()
            self.tx_buffer.clear()
            self.streamer.set_capturing(True)
            self.signal_drop_time = time.time() + duration

    async def _telemetry_broadcast_loop(self):
        """Stream real-time status and VU levels to Web UI clients at 25Hz."""
        while self.running:
            if self.active_websockets:
                try:
                    telemetry = self.radio.poll_telemetry()
                    vu_levels = self.streamer.get_vu_levels()
                    cfg = config_manager.get()
                    storage = disk_manager.get_storage_stats()

                    payload = {
                        "type": "telemetry",
                        "state": self.state,
                        "radio": telemetry,
                        "vu": vu_levels,
                        "openai_connected": self.openai_client.is_connected,
                        "threshold": cfg.s_meter_threshold,
                        "callsign": cfg.callsign,
                        "user_transcript": self.latest_user_transcript,
                        "ai_transcript": self.latest_ai_transcript,
                        "storage": storage,
                    }

                    dead_sockets = set()
                    for ws in self.active_websockets:
                        try:
                            await ws.send_json(payload)
                        except Exception:
                            dead_sockets.add(ws)

                    self.active_websockets -= dead_sockets
                except Exception as e:
                    logger.debug(f"Telemetry broadcast error: {e}")

            await asyncio.sleep(0.04)

    def register_websocket(self, ws: WebSocket):
        self.active_websockets.add(ws)

    def unregister_websocket(self, ws: WebSocket):
        self.active_websockets.discard(ws)

    async def stop(self):
        self.running = False
        if self._main_task:
            self._main_task.cancel()
        if self._telemetry_task:
            self._telemetry_task.cancel()
        self.radio.set_ptt(False)
        self.radio.disconnect()
        self.streamer.stop()
        await self.openai_client.disconnect()


orchestrator = TransceiverOrchestrator()
