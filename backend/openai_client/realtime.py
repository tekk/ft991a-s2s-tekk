"""
OpenAI Realtime Speech-to-Speech (S2S) WebSocket Client.
Maintains session, streams PCM16 audio, coordinates half-duplex turn-taking,
and provides live transcripts.
"""

import json
import base64
import asyncio
import logging
import websockets
from typing import Optional, Callable, Dict, Any

from backend.config import config_manager
from backend.openai_client.prompts import generate_system_prompt

logger = logging.getLogger("openai_realtime")

REALTIME_WS_BASE = "wss://api.openai.com/v1/realtime"


class OpenAIRealtimeClient:
    def __init__(self):
        self.ws = None
        self.is_connected = False
        self._receive_task: Optional[asyncio.Task] = None
        self._send_queue: asyncio.Queue = asyncio.Queue()

        # Callbacks
        self.on_audio_delta: Optional[Callable[[bytes], None]] = None
        self.on_user_transcript: Optional[Callable[[str], None]] = None
        self.on_assistant_transcript_delta: Optional[Callable[[str], None]] = None
        self.on_assistant_transcript_done: Optional[Callable[[str], None]] = None
        self.on_response_done: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        self.current_response_text = ""

    async def connect(self) -> bool:
        """Establish WebSocket connection to OpenAI Realtime API."""
        cfg = config_manager.get()
        api_key = cfg.openai_api_key.strip()
        if not api_key:
            logger.warning("OpenAI API key is missing. Realtime S2S client cannot connect.")
            return False

        url = f"{REALTIME_WS_BASE}?model={cfg.model}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        try:
            logger.info(f"Connecting to OpenAI Realtime API at {url}...")
            self.ws = await websockets.connect(
                url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=20,
                max_size=10 * 1024 * 1024,
            )
            self.is_connected = True
            logger.info("Connected to OpenAI Realtime API.")

            # Send session configuration
            await self._update_session()

            # Start background receive task
            if self._receive_task:
                self._receive_task.cancel()
            self._receive_task = asyncio.create_task(self._receive_loop())
            return True
        except Exception as e:
            logger.error(f"OpenAI Realtime connection failed: {e}")
            self.is_connected = False
            self.ws = None
            if self.on_error:
                self.on_error(f"OpenAI connection failed: {e}")
            return False

    async def _update_session(self):
        """Configure OpenAI session with Ham Radio persona and audio formats."""
        cfg = config_manager.get()
        system_prompt = generate_system_prompt(
            callsign=cfg.callsign,
            custom_instructions=cfg.system_prompt_custom,
        )

        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["audio", "text"],
                "instructions": system_prompt,
                "voice": cfg.voice,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": None,  # Manual turn-taking for half-duplex radio PTT
            }
        }
        await self.send_json(session_config)
        logger.info(f"OpenAI Realtime session initialized for station callsign {cfg.callsign}")

    async def send_json(self, data: Dict[str, Any]):
        if self.ws and self.is_connected:
            try:
                await self.ws.send(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending message to OpenAI: {e}")

    async def append_input_audio(self, pcm16_24k_bytes: bytes):
        """Stream an incoming audio chunk (from radio RX) to OpenAI."""
        if not self.is_connected or not pcm16_24k_bytes:
            return

        b64_audio = base64.b64encode(pcm16_24k_bytes).decode("ascii")
        event = {
            "type": "input_audio_buffer.append",
            "audio": b64_audio,
        }
        await self.send_json(event)

    async def commit_and_generate(self):
        """End of incoming transmission. Commit buffer and request AI speech generation."""
        if not self.is_connected:
            return

        logger.info("Committing input audio buffer and requesting AI response...")
        self.current_response_text = ""
        # 1. Commit the audio recorded so far
        await self.send_json({"type": "input_audio_buffer.commit"})
        # 2. Instruct OpenAI to generate response
        await self.send_json({
            "type": "response.create",
            "response": {
                "modalities": ["audio", "text"],
            }
        })

    async def _receive_loop(self):
        """Continuously process events from OpenAI Realtime WebSocket."""
        try:
            async for raw_msg in self.ws:
                event = json.loads(raw_msg)
                event_type = event.get("type", "")

                if event_type == "response.audio.delta":
                    delta_b64 = event.get("delta", "")
                    if delta_b64:
                        pcm_chunk = base64.b64decode(delta_b64)
                        if self.on_audio_delta:
                            self.on_audio_delta(pcm_chunk)

                elif event_type == "response.audio_transcript.delta":
                    text_delta = event.get("delta", "")
                    self.current_response_text += text_delta
                    if self.on_assistant_transcript_delta:
                        self.on_assistant_transcript_delta(text_delta)

                elif event_type == "response.audio_transcript.done":
                    transcript = event.get("transcript", self.current_response_text)
                    if self.on_assistant_transcript_done:
                        self.on_assistant_transcript_done(transcript)

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    user_transcript = event.get("transcript", "")
                    if user_transcript and self.on_user_transcript:
                        self.on_user_transcript(user_transcript)

                elif event_type == "response.done":
                    logger.info("OpenAI response audio generation completed.")
                    if self.on_response_done:
                        self.on_response_done()

                elif event_type == "error":
                    error_info = event.get("error", {})
                    msg = error_info.get("message", "Unknown OpenAI Realtime error")
                    logger.error(f"OpenAI Realtime Error: {msg}")
                    if self.on_error:
                        self.on_error(msg)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Exception in OpenAI receive loop: {e}")
            self.is_connected = False
        finally:
            self.is_connected = False
            logger.info("OpenAI Realtime receive loop stopped.")

    async def disconnect(self):
        self.is_connected = False
        if self._receive_task:
            self._receive_task.cancel()
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None
        logger.info("Disconnected from OpenAI Realtime API.")
