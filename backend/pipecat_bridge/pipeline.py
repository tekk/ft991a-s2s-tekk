"""
Master Pipecat Pipeline Coordinator for Yaesu FT-991A.
Assembles the complete voice pipeline:
Transport.input() -> Security -> STT -> LLM (with Skills) -> Security -> TTS -> Transport.output()
Handles state machine, recordings, telemetry, and background runner.
"""

import time
import asyncio
import logging
from typing import Optional, Dict, Any, List

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.pipeline.runner import PipelineRunner
from pipecat.frames.frames import TextFrame

from backend.config import config_manager
from backend.cat.base import BaseRadio
from backend.cat.ft991a import FT991ARadio
from backend.cat.mock_radio import MockRadio
from backend.recording.recorder import audio_recorder
from backend.pipecat_bridge.transport import RadioAudioTransport
from backend.pipecat_bridge.processors import (
    SecurityGuardrailProcessor,
    TranscriptLoggerProcessor,
    PTTPlaybackGaterProcessor,
)
from backend.pipecat_bridge.services_factory import (
    create_stt_service,
    create_llm_service,
    create_tts_service,
    create_realtime_service,
)
from backend.pipecat_bridge.skills import skill_manager

logger = logging.getLogger("pipecat_pipeline")


class PipecatRadioBridge:
    """Master controller orchestrating the Yaesu FT-991A radio and Pipecat audio pipeline."""

    def __init__(self):
        self.radio: Optional[BaseRadio] = None
        self.transport: Optional[RadioAudioTransport] = None
        self.pipeline: Optional[Pipeline] = None
        self.task: Optional[PipelineTask] = None
        self.runner: Optional[PipelineRunner] = None
        self.sample_rate = 16000

        self.running = False
        self.current_state = "IDLE"  # IDLE, RX, PROCESSING, TX
        self.latest_user_transcript = ""
        self.latest_ai_transcript = ""
        self.transmission_log: List[Dict[str, Any]] = []
        self._ws_clients = []
        self._runner_task: Optional[asyncio.Task] = None
        self._telemetry_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Build and configure the Pipecat pipeline and transceiver connections."""
        cfg = config_manager.get()
        logger.info(f"Initializing Pipecat Radio Bridge (Callsign: {cfg.callsign})...")

        # 1. Connect Radio
        if cfg.simulated_mode:
            self.radio = MockRadio()
        else:
            self.radio = FT991ARadio()
        self.radio.connect()

        # 2. Setup Radio Audio Transport
        self.transport = RadioAudioTransport(
            radio=self.radio,
            sample_rate=self.sample_rate,
        )

        # Connect recording hooks
        self.transport.input().on_transmission_done = self._handle_rx_done
        self.transport.output().on_transmission_done = self._handle_tx_done

        # 3. Setup Processors
        security_processor = SecurityGuardrailProcessor()
        transcript_logger = TranscriptLoggerProcessor(
            on_user_transcript=self._on_user_transcript,
            on_assistant_transcript=self._on_assistant_transcript,
        )
        ptt_gater = PTTPlaybackGaterProcessor(output_transport=self.transport.output())

        # 4. Determine Pipeline Architecture (Realtime S2S vs Cascaded STT->LLM->TTS)
        processors = [self.transport.input()]

        if cfg.pipeline_mode == "realtime" and cfg.openai_api_key:
            realtime_service = create_realtime_service(cfg)
            if realtime_service:
                logger.info("Assembling OpenAI Realtime S2S Pipecat pipeline.")
                processors.extend([
                    security_processor,
                    realtime_service,
                    transcript_logger,
                    self.transport.output(),
                    ptt_gater,
                ])
            else:
                cfg.pipeline_mode = "cascaded"

        if cfg.pipeline_mode != "realtime" or not cfg.openai_api_key:
            logger.info("Assembling Cascaded STT -> Guardrail -> LLM -> TTS Pipecat pipeline.")
            stt = create_stt_service(cfg, sample_rate=self.sample_rate)
            llm = create_llm_service(cfg)
            tts = create_tts_service(cfg, sample_rate=self.sample_rate)

            processors.extend([
                stt,
                transcript_logger,
                security_processor,
                llm,
                tts,
                self.transport.output(),
                ptt_gater,
            ])

        # 5. Build Pipecat Pipeline & Task
        self.pipeline = Pipeline(processors)
        self.task = PipelineTask(
            self.pipeline,
            params=PipelineParams(allow_interruptions=True),
        )
        self.runner = PipelineRunner()

    async def start(self):
        """Start Pipecat background tasks and hardware capture streams."""
        if self.running:
            return
        self.running = True
        await self.initialize()

        loop = asyncio.get_running_loop()
        self.transport.input().start_capture(loop)
        self.transport.output().start_playback_stream(loop)

        # Run Pipecat PipelineTask in background
        self._runner_task = asyncio.create_task(self._run_pipeline_loop())
        self._telemetry_task = asyncio.create_task(self._telemetry_broadcast_loop())
        logger.info("Pipecat Radio Bridge successfully started.")

    async def _run_pipeline_loop(self):
        try:
            await self.runner.run(self.task)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in Pipecat pipeline runner: {e}", exc_info=True)

    async def _telemetry_broadcast_loop(self):
        """Broadcast live radio & audio status to Web UI, TUI, and Android."""
        while self.running:
            try:
                telemetry = self.radio.poll_telemetry() if self.radio else {}
                cfg = config_manager.get()
                s_meter = telemetry.get("s_meter", 0)

                # Determine active radio state
                if self.transport and self.transport.output().is_transmitting:
                    self.current_state = "TX"
                elif self.transport and self.transport.input().signal_active:
                    self.current_state = "RX"
                else:
                    self.current_state = "IDLE"

                vu = self.get_vu_levels()

                payload = {
                    "state": self.current_state,
                    "s_meter_raw": s_meter,
                    "s_meter_label": telemetry.get("s_meter_label", "S0"),
                    "frequency_hz": telemetry.get("frequency_hz", 14200000),
                    "frequency_str": telemetry.get("frequency_str", "14.20000 MHz"),
                    "mode": telemetry.get("mode", "USB"),
                    "power_watts": telemetry.get("power_watts", 50),
                    "ptt_active": telemetry.get("ptt_active", False),
                    "threshold": cfg.s_meter_threshold,
                    "callsign": cfg.callsign,
                    "user_transcript": self.latest_user_transcript,
                    "ai_transcript": self.latest_ai_transcript,
                    "rx_rms": vu["rx_rms"],
                    "rx_peak": vu["rx_peak"],
                    "tx_rms": vu["tx_rms"],
                    "tx_peak": vu["tx_peak"],
                    "pipeline_mode": cfg.pipeline_mode,
                    "stt_provider": cfg.stt_provider,
                    "llm_provider": cfg.llm_provider,
                    "tts_provider": cfg.tts_provider,
                }

                # Broadcast to connected WebSocket clients (Web UI, Android, Desktop GUI)
                disconnected = []
                for ws in self._ws_clients:
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        disconnected.append(ws)

                for ws in disconnected:
                    if ws in self._ws_clients:
                        self._ws_clients.remove(ws)

            except Exception as e:
                logger.debug(f"Telemetry broadcast exception: {e}")

            await asyncio.sleep(0.08)  # ~12 Hz update rate

    def get_vu_levels(self) -> Dict[str, float]:
        if not self.transport:
            return {"rx_rms": 0.0, "rx_peak": 0.0, "tx_rms": 0.0, "tx_peak": 0.0}
        return {
            "rx_rms": self.transport.input().rx_rms,
            "rx_peak": self.transport.input().rx_peak,
            "tx_rms": self.transport.output().tx_rms,
            "tx_peak": self.transport.output().tx_peak,
        }

    def _on_user_transcript(self, text: str):
        self.latest_user_transcript = text

    def _on_assistant_transcript(self, text: str):
        self.latest_ai_transcript = text

    def _handle_rx_done(self, pcm_bytes: bytes, duration: float):
        """Save received audio recording."""
        asyncio.create_task(self._save_recording(pcm_bytes, "rx", self.latest_user_transcript))

    def _handle_tx_done(self, pcm_bytes: bytes, duration: float):
        """Save transmitted audio recording."""
        asyncio.create_task(self._save_recording(pcm_bytes, "tx", self.latest_ai_transcript))

    async def _save_recording(self, pcm_bytes: bytes, prefix: str, transcript: str):
        try:
            rec_info = await audio_recorder.save_recording(
                pcm_bytes=pcm_bytes,
                sample_rate=self.sample_rate,
                channels=1,
                prefix=prefix,
            )
            if rec_info:
                log_item = {
                    "id": rec_info["filename"],
                    "type": prefix.upper(),
                    "timestamp": time.time(),
                    "duration": rec_info["duration_seconds"],
                    "url": rec_info["url"],
                    "transcript": transcript,
                }
                self.transmission_log.insert(0, log_item)
                if len(self.transmission_log) > 50:
                    self.transmission_log.pop()
        except Exception as e:
            logger.error(f"Error saving recording: {e}")

    def register_websocket(self, ws):
        if ws not in self._ws_clients:
            self._ws_clients.append(ws)

    def unregister_websocket(self, ws):
        if ws in self._ws_clients:
            self._ws_clients.remove(ws)

    def set_manual_ptt(self, active: bool):
        if self.transport:
            self.transport.input().set_manual_ptt(active)
            if not active and self.radio:
                self.radio.set_ptt(False)

    def trigger_simulated_rx(self, duration: float = 4.0):
        if self.radio and isinstance(self.radio, MockRadio):
            self.radio.simulate_signal(duration=duration)
        elif self.transport:
            self.transport.input().set_manual_ptt(True)
            asyncio.create_task(self._stop_simulated_rx_delayed(duration))

    async def _stop_simulated_rx_delayed(self, delay: float):
        await asyncio.sleep(delay)
        if self.transport:
            self.transport.input().set_manual_ptt(False)

    async def reload_configuration(self):
        """Gracefully reloads radio, audio devices, and Pipecat pipeline."""
        logger.info("Reloading Pipecat Radio Bridge configuration...")
        await self.stop()
        await self.start()

    async def stop(self):
        """Clean shutdown of streams, radio, and pipeline runner."""
        self.running = False
        if self._telemetry_task:
            self._telemetry_task.cancel()
        if self.transport:
            self.transport.input().stop()
            self.transport.output().stop()
        if self.radio:
            self.radio.set_ptt(False)
            self.radio.disconnect()
        if self.task:
            await self.task.queue_frame(TextFrame(text=""))
        if self.runner:
            await self.runner.cancel()


# Global singleton instance
pipecat_bridge = PipecatRadioBridge()
