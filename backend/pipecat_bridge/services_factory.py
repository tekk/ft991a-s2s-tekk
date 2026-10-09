"""
Dynamic Pipecat Services Factory.
Builds STT, LLM, TTS, or Realtime services dynamically based on configured API keys,
language parameters, provider preferences, and available skills.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, Tuple

from pipecat.services.ai_service import AIService
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    Frame,
    TextFrame,
    LLMTextFrame,
    TranscriptionFrame,
    AudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    LLMFullResponseEndFrame,
)

from backend.config import AppConfig, config_manager
from backend.openai_client.prompts import HAM_SYSTEM_PROMPT, generate_system_prompt
from backend.pipecat_bridge.skills import skill_manager
from backend.localization import get_spoken_text

logger = logging.getLogger("services_factory")


# --- Simulated Fallback Services (Offline / Testing / Zero-Key mode) ---

class MockSTTService(FrameProcessor):
    """Simulated STT for offline testing or hardware simulation."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, AudioRawFrame) and direction == FrameDirection.DOWNSTREAM:
            # Emit a mock transcription after collecting audio
            pass
        await self.push_frame(frame, direction)


class MockLLMService(FrameProcessor):
    """Simulated LLM responding with standard amateur radio courtesies."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, (TranscriptionFrame, TextFrame)) and direction == FrameDirection.DOWNSTREAM:
            cfg = config_manager.get()
            callsign = cfg.callsign
            text = frame.text if hasattr(frame, "text") else ""
            reply = get_spoken_text(
                "mock_qso_reply",
                language=cfg.language,
                callsign=callsign,
                band="20m",
            )
            await self.push_frame(LLMTextFrame(text=reply), direction)
            await self.push_frame(LLMFullResponseEndFrame(), direction)
            return
        await self.push_frame(frame, direction)


class MockTTSService(FrameProcessor):
    """Simulated TTS producing synthetic audio frames."""
    def __init__(self, sample_rate: int = 16000, **kwargs):
        super().__init__(**kwargs)
        self.sample_rate = sample_rate

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, (LLMTextFrame, TextFrame)) and direction == FrameDirection.DOWNSTREAM:
            await self.push_frame(TTSStartedFrame(), direction)
            import numpy as np
            # Generate 0.5s of audio tone
            duration = 0.5
            t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
            sine = (0.3 * np.sin(2 * np.pi * 600 * t) * 32767).astype(np.int16)
            pcm = sine.tobytes()
            await self.push_frame(AudioRawFrame(audio=pcm, sample_rate=self.sample_rate, num_channels=1), direction)
            await self.push_frame(TTSStoppedFrame(), direction)
            return
        await self.push_frame(frame, direction)


# --- Service Builders ---

def build_system_instruction(cfg: AppConfig) -> str:
    """Build effective system prompt combining base prompt, custom prompt, language, and national regulations."""
    if not cfg.system_prompt.strip():
        base = generate_system_prompt(
            callsign=cfg.callsign,
            custom_instructions=cfg.system_prompt_custom,
            language=cfg.language,
            regulatory_jurisdiction=cfg.regulatory_jurisdiction,
        )
    else:
        base = cfg.system_prompt.strip().format(callsign=cfg.callsign)
        if cfg.system_prompt_custom.strip():
            base += f"\n{cfg.system_prompt_custom.strip()}"

    brevity = "\nKeep answers strictly between 1 and 2 sentences maximum." if cfg.agent_brevity_level == "strict" else ""
    return f"{base}\n{brevity}".strip()


def create_stt_service(cfg: AppConfig, sample_rate: int = 16000) -> FrameProcessor:
    """Instantiate appropriate STT service based on available keys and preferences."""
    pref = cfg.stt_provider.lower()
    lang = cfg.stt_language

    # 1. Deepgram STT
    if (pref == "deepgram" or pref == "auto") and cfg.deepgram_api_key:
        try:
            from pipecat.services.deepgram.stt import DeepgramSTTService
            logger.info("Using Deepgram STT service.")
            return DeepgramSTTService(
                api_key=cfg.deepgram_api_key,
                live_options={"language": lang, "model": "nova-2", "smart_format": True},
            )
        except Exception as e:
            logger.error(f"Failed to create Deepgram STT: {e}")

    # 2. Groq Whisper STT
    if (pref == "groq" or pref == "auto") and cfg.groq_api_key:
        try:
            from pipecat.services.groq.stt import GroqSTTService
            logger.info("Using Groq Whisper STT service.")
            return GroqSTTService(
                api_key=cfg.groq_api_key,
                language=lang,
            )
        except Exception as e:
            logger.error(f"Failed to create Groq STT: {e}")

    # 3. OpenAI STT
    if (pref == "openai" or pref == "auto") and cfg.openai_api_key:
        try:
            from pipecat.services.openai.stt import OpenAISTTService
            logger.info("Using OpenAI STT service.")
            return OpenAISTTService(
                api_key=cfg.openai_api_key,
                language=lang,
            )
        except Exception as e:
            logger.error(f"Failed to create OpenAI STT: {e}")

    logger.warning("No STT API keys configured or simulation mode active. Using MockSTTService.")
    return MockSTTService()


def create_llm_service(cfg: AppConfig) -> FrameProcessor:
    """Instantiate appropriate LLM service based on available keys and preferences."""
    pref = cfg.llm_provider.lower()
    system_instruction = build_system_instruction(cfg)

    # 1. Anthropic LLM
    if (pref == "anthropic" or (pref == "auto" and not cfg.openai_api_key)) and cfg.anthropic_api_key:
        try:
            from pipecat.services.anthropic.llm import AnthropicLLMService
            logger.info("Using Anthropic LLM service (Claude).")
            return AnthropicLLMService(
                api_key=cfg.anthropic_api_key,
                model="claude-3-5-sonnet-20241022",
                system=system_instruction,
            )
        except Exception as e:
            logger.error(f"Failed to create Anthropic LLM: {e}")

    # 2. Groq LLM
    if (pref == "groq" or (pref == "auto" and not cfg.openai_api_key)) and cfg.groq_api_key:
        try:
            from pipecat.services.groq.llm import GroqLLMService
            logger.info("Using Groq LLM service (Llama).")
            return GroqLLMService(
                api_key=cfg.groq_api_key,
                model="llama-3.3-70b-versatile",
            )
        except Exception as e:
            logger.error(f"Failed to create Groq LLM: {e}")

    # 3. Google Gemini LLM
    if (pref == "google" or (pref == "auto" and not cfg.openai_api_key)) and cfg.google_api_key:
        try:
            from pipecat.services.google.llm import GoogleLLMService
            logger.info("Using Google Gemini LLM service.")
            return GoogleLLMService(
                api_key=cfg.google_api_key,
                model="gemini-2.0-flash",
                system_instruction=system_instruction,
            )
        except Exception as e:
            logger.error(f"Failed to create Google LLM: {e}")

    # 4. Ollama LLM (Local)
    if pref == "ollama" or (pref == "auto" and not cfg.openai_api_key and not cfg.anthropic_api_key and not cfg.groq_api_key):
        try:
            from pipecat.services.ollama.llm import OLLamaLLMService
            logger.info(f"Using local Ollama LLM on {cfg.ollama_host}.")
            return OLLamaLLMService(
                model="llama3.2",
                base_url=cfg.ollama_host,
            )
        except Exception as e:
            logger.debug(f"Ollama local LLM not available: {e}")

    # 5. OpenAI LLM (Default)
    if cfg.openai_api_key:
        try:
            from pipecat.services.openai.llm import OpenAILLMService
            logger.info("Using OpenAI LLM service.")
            return OpenAILLMService(
                api_key=cfg.openai_api_key,
                model="gpt-4o-mini",
            )
        except Exception as e:
            logger.error(f"Failed to create OpenAI LLM: {e}")

    logger.warning("No LLM API keys configured. Using MockLLMService.")
    return MockLLMService()


def create_tts_service(cfg: AppConfig, sample_rate: int = 16000) -> FrameProcessor:
    """Instantiate appropriate TTS service based on available keys and preferences."""
    pref = cfg.tts_provider.lower()

    # 1. Cartesia TTS
    if (pref == "cartesia" or pref == "auto") and cfg.cartesia_api_key:
        try:
            from pipecat.services.cartesia.tts import CartesiaTTSService
            logger.info("Using Cartesia ultra-low latency TTS service.")
            return CartesiaTTSService(
                api_key=cfg.cartesia_api_key,
                voice_id=cfg.voice if cfg.voice != "alloy" else "86e30c1d-714b-4074-a1f2-1cb6b552fb49",
                sample_rate=sample_rate,
            )
        except Exception as e:
            logger.error(f"Failed to create Cartesia TTS: {e}")

    # 2. ElevenLabs TTS
    if (pref == "elevenlabs" or (pref == "auto" and not cfg.cartesia_api_key)) and cfg.elevenlabs_api_key:
        try:
            from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
            logger.info("Using ElevenLabs TTS service.")
            return ElevenLabsTTSService(
                api_key=cfg.elevenlabs_api_key,
                voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
                sample_rate=sample_rate,
            )
        except Exception as e:
            logger.error(f"Failed to create ElevenLabs TTS: {e}")

    # 3. Deepgram TTS
    if (pref == "deepgram" or (pref == "auto" and not cfg.cartesia_api_key and not cfg.elevenlabs_api_key)) and cfg.deepgram_api_key:
        try:
            from pipecat.services.deepgram.tts import DeepgramTTSService
            logger.info("Using Deepgram Aura TTS service.")
            return DeepgramTTSService(
                api_key=cfg.deepgram_api_key,
                voice="aura-helios-en",
                sample_rate=sample_rate,
            )
        except Exception as e:
            logger.error(f"Failed to create Deepgram TTS: {e}")

    # 4. OpenAI TTS
    if cfg.openai_api_key:
        try:
            from pipecat.services.openai.tts import OpenAITTSService
            logger.info("Using OpenAI TTS service.")
            return OpenAITTSService(
                api_key=cfg.openai_api_key,
                voice=cfg.voice,
                sample_rate=sample_rate,
            )
        except Exception as e:
            logger.error(f"Failed to create OpenAI TTS: {e}")

    logger.warning("No TTS API keys configured. Using MockTTSService.")
    return MockTTSService(sample_rate=sample_rate)


def create_realtime_service(cfg: AppConfig) -> Optional[FrameProcessor]:
    """Create OpenAI Realtime speech-to-speech service if API key is present."""
    if not cfg.openai_api_key:
        return None

    try:
        from pipecat.services.openai.realtime.llm import OpenAIRealtimeLLMService
        system_instruction = build_system_instruction(cfg)
        logger.info("Using OpenAI Realtime S2S service.")
        return OpenAIRealtimeLLMService(
            api_key=cfg.openai_api_key,
            model=cfg.model,
            voice=cfg.voice,
            system_instruction=system_instruction,
        )
    except Exception as e:
        logger.error(f"Failed to create OpenAI Realtime service: {e}")
        return None
