"""
Configuration Manager for FT-991A AI S2S Transceiver System.
Loads from environment variables and persists to data/config.json.
Supports multiple STT, LLM, TTS providers, languages, prompt editing, and device preferences.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = BASE_DIR / "recordings"
CONFIG_FILE = DATA_DIR / "config.json"
SKILLS_FILE = DATA_DIR / "skills.json"


class AppConfig(BaseModel):
    # Multi-Provider API Keys
    openai_api_key: str = Field(default="", description="OpenAI API key")
    deepgram_api_key: str = Field(default="", description="Deepgram API key")
    cartesia_api_key: str = Field(default="", description="Cartesia API key")
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API key")
    groq_api_key: str = Field(default="", description="Groq API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    google_api_key: str = Field(default="", description="Google/Gemini API key")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama API Host")

    # Engine & Provider Preferences
    pipeline_mode: str = Field(default="auto", description="Pipeline mode: auto, realtime (OpenAI), cascaded (STT->LLM->TTS)")
    stt_provider: str = Field(default="auto", description="STT Provider: auto, deepgram, openai, groq, whisper")
    llm_provider: str = Field(default="auto", description="LLM Provider: auto, openai, anthropic, groq, google, ollama")
    tts_provider: str = Field(default="auto", description="TTS Provider: auto, cartesia, elevenlabs, openai, deepgram")

    # Model & Voice IDs
    model: str = Field(default="gpt-4o-realtime-preview-2024-12-17", description="Default/Active LLM Model ID")
    voice: str = Field(default="alloy", description="Default/Active Voice ID or name")
    openai_model: str = Field(default="gpt-4o", description="OpenAI LLM Model")
    groq_model: str = Field(default="llama-3.3-70b-versatile", description="Groq Model")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", description="Anthropic Model")
    google_model: str = Field(default="gemini-2.0-flash", description="Google Model")
    ollama_model: str = Field(default="llama3.2", description="Ollama Model")
    cartesia_voice_id: str = Field(default="a0e99841-438c-4a64-b679-ae501e7d6091", description="Cartesia Voice ID")
    elevenlabs_voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM", description="ElevenLabs Voice ID")
    
    # Language Configuration
    stt_language: str = Field(default="en", description="STT language code (en, es, de, fr, ja, it, etc.)")
    tts_language: str = Field(default="en", description="TTS language code")

    # Prompt & Persona Configuration
    system_prompt: str = Field(default="", description="Active base system prompt (empty for default amateur radio)")
    system_prompt_custom: str = Field(default="", description="Custom addendum to Ham system prompt")
    custom_system_prompt: str = Field(default="", description="Custom system prompt override")
    agent_brevity_level: str = Field(default="strict", description="Agent brevity: strict (1-2 sentences), moderate, detailed")
    security_level: str = Field(default="high", description="Anti-injection & content security: high, medium, off")

    # Radio & Station Settings
    callsign: str = Field(default="AI7HAM", description="Amateur radio callsign")
    serial_port: str = Field(default="/dev/ttyUSB0", description="FT-991A CAT Serial Port")
    auto_serial_port: bool = Field(default=True, description="Automatically probe and detect FT-991A serial port")
    preferred_serial_port: Optional[str] = Field(default=None, description="Preferred serial port if multiple found")
    baud_rate: int = Field(default=38400, description="CAT Baud Rate (4800, 9600, 19200, 38400)")
    s_meter_threshold: int = Field(default=80, description="Raw CAT S-Meter trigger threshold (0-255, 80 ~= S4)")
    ptt_mode: str = Field(default="CAT", description="PTT trigger method: CAT (TX1;/TX0;), DATA_CAT (TX2;/TX0;), RTS, or DTR")

    # Audio Devices
    audio_input_device: Optional[str] = Field(default=None, description="Input sound card name or index")
    audio_output_device: Optional[str] = Field(default=None, description="Output sound card name or index")
    preferred_audio_in: Optional[str] = Field(default=None, description="Preferred audio input device pattern")
    preferred_audio_out: Optional[str] = Field(default=None, description="Preferred audio output device pattern")

    # Timing & Safety Settings
    rx_hang_time_ms: int = Field(default=800, description="Hang time before committing RX after signal drops below S4")
    pre_tx_delay_ms: int = Field(default=200, description="Delay between keying PTT and sending audio to settle relays")
    post_tx_delay_ms: int = Field(default=250, description="Delay between audio stream end and unkeying PTT")
    max_tx_duration_sec: int = Field(default=30, description="Safety watchdog maximum continuous TX seconds")

    # Audio Recording & SBC Storage Watchdog
    recordings_enabled: bool = Field(default=True, description="Save RX and TX recordings to disk")
    recording_format: str = Field(default="opus", description="Compression format: opus, mp3, ogg, m4a")
    recording_bitrate: str = Field(default="32k", description="Encoding bitrate: 24k, 32k, 64k, 128k")
    min_free_disk_mb: int = Field(default=500, description="Minimum free disk space threshold before rolling purge")
    max_recordings_mb: int = Field(default=5000, description="Maximum disk space allocated for recordings")

    # Network / Web Server
    port: int = Field(default=80, description="Target Web UI port")
    host: str = Field(default="0.0.0.0", description="Target Web UI host binding")

    # Hardware Emulation / Testing
    simulated_mode: bool = Field(default=False, description="Simulate FT-991A radio hardware")

    def _mask_key(self, key: str) -> str:
        if not key:
            return ""
        if len(key) > 8:
            return f"{key[:3]}...{key[-4:]}"
        return "***"

    def masked_dict(self) -> Dict[str, Any]:
        """Return dict with sensitive fields like API keys masked."""
        d = self.model_dump()
        
        # Mask all API keys
        d["openai_api_key_masked"] = self._mask_key(d.get("openai_api_key", ""))
        d["has_api_key"] = bool(d.get("openai_api_key"))  # Backward compatibility
        d["has_openai_key"] = bool(d.get("openai_api_key"))
        
        d["deepgram_api_key_masked"] = self._mask_key(d.get("deepgram_api_key", ""))
        d["has_deepgram_key"] = bool(d.get("deepgram_api_key"))
        
        d["cartesia_api_key_masked"] = self._mask_key(d.get("cartesia_api_key", ""))
        d["has_cartesia_key"] = bool(d.get("cartesia_api_key"))
        
        d["elevenlabs_api_key_masked"] = self._mask_key(d.get("elevenlabs_api_key", ""))
        d["has_elevenlabs_key"] = bool(d.get("elevenlabs_api_key"))
        
        d["groq_api_key_masked"] = self._mask_key(d.get("groq_api_key", ""))
        d["has_groq_key"] = bool(d.get("groq_api_key"))
        
        d["anthropic_api_key_masked"] = self._mask_key(d.get("anthropic_api_key", ""))
        d["has_anthropic_key"] = bool(d.get("anthropic_api_key"))
        
        d["google_api_key_masked"] = self._mask_key(d.get("google_api_key", ""))
        d["has_google_key"] = bool(d.get("google_api_key"))

        # Available provider summary for UI
        d["available_providers"] = {
            "openai": d["has_openai_key"],
            "deepgram": d["has_deepgram_key"],
            "cartesia": d["has_cartesia_key"],
            "elevenlabs": d["has_elevenlabs_key"],
            "groq": d["has_groq_key"],
            "anthropic": d["has_anthropic_key"],
            "google": d["has_google_key"],
            "ollama": True,  # local
        }
        return d


class ConfigManager:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self._load()

    def _load(self) -> AppConfig:
        config_data = {}

        # 1. Defaults from environment variables
        env_mappings = {
            "OPENAI_API_KEY": ("openai_api_key", str),
            "DEEPGRAM_API_KEY": ("deepgram_api_key", str),
            "CARTESIA_API_KEY": ("cartesia_api_key", str),
            "ELEVENLABS_API_KEY": ("elevenlabs_api_key", str),
            "GROQ_API_KEY": ("groq_api_key", str),
            "ANTHROPIC_API_KEY": ("anthropic_api_key", str),
            "GOOGLE_API_KEY": ("google_api_key", str),
            "GEMINI_API_KEY": ("google_api_key", str),
            "OLLAMA_HOST": ("ollama_host", str),
            "PIPELINE_MODE": ("pipeline_mode", str),
            "STT_PROVIDER": ("stt_provider", str),
            "LLM_PROVIDER": ("llm_provider", str),
            "TTS_PROVIDER": ("tts_provider", str),
            "STT_LANGUAGE": ("stt_language", str),
            "TTS_LANGUAGE": ("tts_language", str),
            "CALLSIGN": ("callsign", str),
            "SERIAL_PORT": ("serial_port", str),
            "AUTO_SERIAL_PORT": ("auto_serial_port", lambda v: v.lower() in ("true", "1", "yes")),
            "BAUD_RATE": ("baud_rate", int),
            "AUDIO_INPUT_DEVICE": ("audio_input_device", str),
            "AUDIO_OUTPUT_DEVICE": ("audio_output_device", str),
            "S_METER_THRESHOLD": ("s_meter_threshold", int),
            "RX_HANG_TIME_MS": ("rx_hang_time_ms", int),
            "PRE_TX_DELAY_MS": ("pre_tx_delay_ms", int),
            "POST_TX_DELAY_MS": ("post_tx_delay_ms", int),
            "MAX_TX_DURATION_SEC": ("max_tx_duration_sec", int),
            "RECORDINGS_ENABLED": ("recordings_enabled", lambda v: v.lower() in ("true", "1", "yes")),
            "RECORDING_FORMAT": ("recording_format", str),
            "RECORDING_BITRATE": ("recording_bitrate", str),
            "MIN_FREE_DISK_MB": ("min_free_disk_mb", int),
            "MAX_RECORDINGS_MB": ("max_recordings_mb", int),
            "PORT": ("port", int),
            "HOST": ("host", str),
            "SIMULATED_MODE": ("simulated_mode", lambda v: v.lower() in ("true", "1", "yes")),
            "SYSTEM_PROMPT": ("system_prompt", str),
            "SECURITY_LEVEL": ("security_level", str),
            "AGENT_BREVITY_LEVEL": ("agent_brevity_level", str),
        }

        for env_var, (field_name, parser) in env_mappings.items():
            val = os.getenv(env_var)
            if val is not None and val != "":
                try:
                    config_data[field_name] = parser(val)
                except Exception:
                    pass

        # 2. Layer on JSON config file if present
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    config_data.update(file_data)
            except Exception as e:
                print(f"[WARN] Error reading {CONFIG_FILE}: {e}")

        return AppConfig(**config_data)

    def save(self, updates: Dict[str, Any]) -> AppConfig:
        """Update and persist configuration to disk."""
        current_data = self.config.model_dump()
        for k, v in updates.items():
            if k in current_data and v is not None:
                current_data[k] = v

        self.config = AppConfig(**current_data)
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config.model_dump(), f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save {CONFIG_FILE}: {e}")

        return self.config

    def get(self) -> AppConfig:
        return self.config


# Global singleton
config_manager = ConfigManager()
