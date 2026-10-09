"""
Mock FT-991A Radio Simulator.
Provides realistic S-meter telemetry, frequency, mode, and PTT state
without requiring physical transceiver hardware.
"""

import time
import random
import logging
from typing import Dict, Any
from backend.cat.base import BaseRadio
from backend.cat.ft991a import raw_smeter_to_label, format_frequency

from backend.config import config_manager

logger = logging.getLogger("mock_radio")


def get_band_for_frequency(hz: int) -> str:
    mhz = hz / 1_000_000.0
    if 144.0 <= mhz <= 148.0:
        return "VHF"
    elif 430.0 <= mhz <= 450.0:
        return "UHF"
    elif 50.0 <= mhz <= 54.0:
        return "6M"
    elif 1.8 <= mhz <= 30.0:
        return "HF"
    return "OTHER"


class MockRadio(BaseRadio):
    def __init__(self, frequency_hz: Optional[int] = None, mode: Optional[str] = None):
        cfg = config_manager.get()
        self._connected = True
        self._ptt_active = False
        self._frequency_hz = frequency_hz if frequency_hz is not None else 14205000
        self._mode = mode.upper() if mode is not None else "USB"
        self._power_watts = 100
        self._simulated_signal_until = 0.0
        self._simulated_signal_level = 145  # S7
        self._repeater_offset_mhz = cfg.vhf_offset_mhz if get_band_for_frequency(self._frequency_hz) == "VHF" else cfg.uhf_offset_mhz
        self._repeater_offset_enabled = cfg.repeater_offset_enabled

    def connect(self) -> bool:
        self._connected = True
        logger.info("Mock FT-991A Radio connected.")
        return True

    def disconnect(self):
        self._connected = False
        self._ptt_active = False
        logger.info("Mock FT-991A Radio disconnected.")

    def is_connected(self) -> bool:
        return self._connected

    def trigger_simulated_transmission(self, duration_sec: float = 4.0, raw_level: int = 145):
        """Simulate an incoming radio transmission breaking squelch / S-meter."""
        self._simulated_signal_level = raw_level
        self._simulated_signal_until = time.time() + duration_sec
        logger.info(f"Simulating incoming transmission for {duration_sec}s (S-meter: {raw_level})")

    def set_ptt(self, transmit: bool) -> bool:
        self._ptt_active = transmit
        logger.info(f"[MOCK RADIO] Transceiver PTT set to: {'TRANSMIT (ON)' if transmit else 'RECEIVE (OFF)'}")
        return True

    def set_frequency(self, freq_hz: int) -> bool:
        self._frequency_hz = int(freq_hz)
        cfg = config_manager.get()
        band = get_band_for_frequency(self._frequency_hz)
        if band == "VHF":
            self._repeater_offset_mhz = cfg.vhf_offset_mhz
        elif band == "UHF":
            self._repeater_offset_mhz = cfg.uhf_offset_mhz
        logger.info(f"[MOCK RADIO] Frequency set to {freq_hz} Hz ({format_frequency(freq_hz)}), band: {band}")
        return True

    def set_mode(self, mode: str) -> bool:
        self._mode = mode.upper()
        logger.info(f"[MOCK RADIO] Mode set to {self._mode}")
        return True

    def set_repeater_offset(self, offset_mhz: float, enabled: bool):
        self._repeater_offset_mhz = float(offset_mhz)
        self._repeater_offset_enabled = bool(enabled)
        logger.info(f"[MOCK RADIO] Repeater offset: {offset_mhz} MHz (enabled: {enabled})")

    def get_tx_frequency(self) -> int:
        if self._repeater_offset_enabled:
            return max(100000, self._frequency_hz + int(self._repeater_offset_mhz * 1_000_000))
        return self._frequency_hz

    def poll_telemetry(self) -> Dict[str, Any]:
        now = time.time()
        if now < self._simulated_signal_until:
            # Active simulated transmission
            s_val = self._simulated_signal_level + random.randint(-4, 4)
        else:
            # Background band noise (S1-S2: ~20-35)
            s_val = random.randint(22, 34)

        band = get_band_for_frequency(self._frequency_hz)
        tx_freq = self.get_tx_frequency()

        return {
            "s_meter": s_val,
            "s_meter_level": raw_smeter_to_label(s_val),
            "frequency_hz": self._frequency_hz,
            "frequency_formatted": format_frequency(self._frequency_hz),
            "tx_frequency_hz": tx_freq,
            "tx_frequency_formatted": format_frequency(tx_freq),
            "repeater_offset_mhz": self._repeater_offset_mhz,
            "repeater_offset_enabled": self._repeater_offset_enabled,
            "band": band,
            "mode": self._mode,
            "power_watts": self._power_watts,
            "ptt_active": self._ptt_active,
            "connected": self._connected,
        }

    def send_raw_command(self, cmd: str) -> str:
        cmd_clean = cmd.strip().upper()
        if cmd_clean.startswith("ID"):
            return "ID0670;"  # FT-991A ID
        elif cmd_clean.startswith("FA"):
            if len(cmd_clean) >= 11 and cmd_clean[2:11].isdigit():
                self._frequency_hz = int(cmd_clean[2:11])
            return f"FA{self._frequency_hz:09d};"
        elif cmd_clean.startswith("MD0"):
            if len(cmd_clean) >= 4:
                # Mode code
                pass
            return "MD02;"  # USB
        elif cmd_clean.startswith("PC"):
            return f"PC{self._power_watts:03d};"
        elif cmd_clean.startswith("TX1"):
            self._ptt_active = True
            return "TX1;"
        elif cmd_clean.startswith("TX0"):
            self._ptt_active = False
            return "TX0;"
        return ";"

