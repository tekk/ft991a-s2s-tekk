"""
Pipecat FrameProcessors for Radio Security, Transcription Logging, and PTT Synchronization.
"""

import logging
from typing import Callable, Optional

from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame,
    TextFrame,
    LLMTextFrame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    LLMFullResponseEndFrame,
)

from backend.pipecat_bridge.security import security_guardrail
from backend.config import config_manager

logger = logging.getLogger("radio_processors")


class SecurityGuardrailProcessor(FrameProcessor):
    """
    Filters incoming STT text against prompt injections, trolling, and NSFW language.
    Sanitizes outgoing LLM speech to guarantee Part 97 brevity and compliance.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.blocked_turn = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        cfg = config_manager.get()
        callsign = cfg.callsign

        # 1. Incoming STT Transcription Inspection
        if isinstance(frame, (TranscriptionFrame, TextFrame)) and direction == FrameDirection.DOWNSTREAM:
            text = frame.text if hasattr(frame, "text") else ""
            if text:
                is_safe, reason, refusal = security_guardrail.inspect_input(text, callsign=callsign)
                if not is_safe:
                    logger.warning(f"SecurityGuardrailProcessor: Blocked '{text}' (Reason: {reason})")
                    self.blocked_turn = True
                    # Push refusal text frame directly downstream to TTS, bypassing LLM
                    await self.push_frame(TextFrame(text=refusal or f"{callsign}: Negative copy."), direction)
                    return

        # 2. Outgoing LLM Text Sanitization
        elif isinstance(frame, (LLMTextFrame, TextFrame)) and direction == FrameDirection.DOWNSTREAM:
            if self.blocked_turn:
                # Turn was blocked, ignore downstream LLM text
                return
            text = frame.text if hasattr(frame, "text") else ""
            if text:
                max_sentences = 2 if cfg.agent_brevity_level == "strict" else 3
                is_valid, sanitized = security_guardrail.sanitize_output(text, callsign=callsign, max_sentences=max_sentences)
                if is_valid and sanitized:
                    frame.text = sanitized

        await self.push_frame(frame, direction)


class TranscriptLoggerProcessor(FrameProcessor):
    """Logs transcript deltas and completed exchanges for UI, TUI, and Android telemetry."""

    def __init__(
        self,
        on_user_transcript: Optional[Callable[[str], None]] = None,
        on_assistant_transcript: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.on_user_transcript = on_user_transcript
        self.on_assistant_transcript = on_assistant_transcript
        self.current_user_text = ""
        self.current_ai_text = ""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, (TranscriptionFrame, TextFrame)):
            self.current_user_text = frame.text
            if self.on_user_transcript:
                self.on_user_transcript(frame.text)

        elif isinstance(frame, LLMTextFrame):
            self.current_ai_text += frame.text
            if self.on_assistant_transcript:
                self.on_assistant_transcript(self.current_ai_text)

        elif isinstance(frame, LLMFullResponseEndFrame):
            if self.on_assistant_transcript and self.current_ai_text:
                self.on_assistant_transcript(self.current_ai_text)
            self.current_ai_text = ""

        await self.push_frame(frame, direction)


class PTTPlaybackGaterProcessor(FrameProcessor):
    """Triggers RadioOutputTransport.finish_turn() once TTS output stream is done."""

    def __init__(self, output_transport, **kwargs):
        super().__init__(**kwargs)
        self.output_transport = output_transport

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, (TTSStoppedFrame, LLMFullResponseEndFrame)):
            # Schedule turn finalization (draining audio and releasing PTT)
            await self.output_transport.finish_turn()

        await self.push_frame(frame, direction)
