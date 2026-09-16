"""
Configuration Manager for FT-991A AI S2S Transceiver System.
Loads from environment variables and persists to data/config.json.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = BASE_DIR / "recordings"
CONFIG_FILE = DATA_DIR / "config.json"


class AppConfig(BaseModel):
    # OpenAI Settings
    openai_api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4o-realtime-preview-2024-12-17", description="Realtime Model ID")
    voice: str = Field(default="alloy", description="OpenAI Voice (alloy, echo, shimmer, ash, ballad, coral, sage, verse)")
    system_prompt_custom: str = Field(default="", description="Custom addendum to Ham system prompt")

    # Radio & Station Settings
    callsign: str = Field(default="AI7HAM", description="Amateur radio callsign")
    serial_port: str = Field(default="/dev/ttyUSB0", description="FT-991A CAT Serial Port")
    baud_rate: int = Field(default=38400, description="CAT Baud Rate (4800, 9600, 19200, 38400)")
    s_meter_threshold: int = Field(default=80, description="Raw CAT S-Meter trigger threshold (0-255, 80 ~= S4)")
    ptt_mode: str = Field(default="CAT", description="PTT trigger method: CAT (TX1;/TX0;), DATA_CAT (TX2;/TX0;), RTS, or DTR")

    # Audio Devices
    audio_input_device: Optional[str] = Field(default=None, description="Input sound card name or index")
    audio_output_device: Optional[str] = Field(default=None, description="Output sound card name or index")

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

    def masked_dict(self) -> Dict[str, Any]:
        """Return dict with sensitive fields like API keys masked."""
        d = self.model_dump()
        if d.get("openai_api_key"):
            key = d["openai_api_key"]
            if len(key) > 8:
                d["openai_api_key_masked"] = f"{key[:3]}...{key[-4:]}"
            else:
                d["openai_api_key_masked"] = "***"
            d["has_api_key"] = True
        else:
            d["openai_api_key_masked"] = ""
            d["has_api_key"] = False
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
            "CALLSIGN": ("callsign", str),
            "SERIAL_PORT": ("serial_port", str),
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
