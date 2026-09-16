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

logger = logging.getLogger("mock_radio")

class MockRadio(BaseRadio):
    def __init__(self):
        self._connected = True
        self._ptt_active = False
        self._frequency_hz = 14205000  # 14.205 MHz (20m Ham Band)
        self._mode = "USB"
        self._power_watts = 100
        self._simulated_signal_until = 0.0
        self._simulated_signal_level = 145  # S7

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

    def poll_telemetry(self) -> Dict[str, Any]:
        now = time.time()
        if now < self._simulated_signal_until:
            # Active simulated transmission
            s_val = self._simulated_signal_level + random.randint(-4, 4)
        else:
            # Background band noise (S1-S2: ~20-35)
            s_val = random.randint(22, 34)

        return {
            "s_meter": s_val,
            "s_meter_level": raw_smeter_to_label(s_val),
            "frequency_hz": self._frequency_hz,
            "frequency_formatted": format_frequency(self._frequency_hz),
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
            return f"FA{self._frequency_hz:09d};"
        elif cmd_clean.startswith("MD0"):
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
