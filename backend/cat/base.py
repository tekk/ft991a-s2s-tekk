"""
Base Radio Interface for CAT Control.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseRadio(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the transceiver CAT port."""
        pass

    @abstractmethod
    def disconnect(self):
        """Safely disconnect and release any PTT locks."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if connection is active."""
        pass

    @abstractmethod
    def poll_telemetry(self) -> Dict[str, Any]:
        """
        Poll radio status.
        Returns dict with:
          - s_meter: int (0-255)
          - s_meter_level: str (e.g. 'S3', 'S9+20dB')
          - frequency_hz: int
          - frequency_formatted: str (e.g. '14.250.00 MHz')
          - mode: str (e.g. 'USB', 'FM')
          - power_watts: int
          - ptt_active: bool
          - connected: bool
        """
        pass

    @abstractmethod
    def set_ptt(self, transmit: bool) -> bool:
        """Engage or disengage Push-To-Talk."""
        pass

    @abstractmethod
    def set_frequency(self, freq_hz: int) -> bool:
        """Set radio VFO frequency in Hz."""
        pass

    @abstractmethod
    def set_mode(self, mode: str) -> bool:
        """Set radio operating mode (FM, USB, LSB, AM, C4FM, etc.)."""
        pass

    @abstractmethod
    def set_repeater_offset(self, offset_mhz: float, enabled: bool):
        """Configure repeater offset in MHz and enable/disable TX offset shift."""
        pass

    @abstractmethod
    def get_tx_frequency(self) -> int:
        """Return the calculated or active transmit frequency in Hz."""
        pass

    @abstractmethod
    def send_raw_command(self, cmd: str) -> str:
        """Send raw CAT command and return response."""
        pass

