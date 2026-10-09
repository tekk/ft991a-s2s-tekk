"""
Yaesu FT-991A CAT Serial Controller.
Communicates with transceiver over USB virtual serial port (Enhanced Port).
Handles S-Meter polling (SM0;), frequency (FA;), mode (MD0;), power (PC;),
and Push-to-Talk (TX1;/TX0;) with a safety watchdog timer.
"""

import time
import serial
import serial.tools.list_ports
import threading
import logging
from typing import Dict, Any, List, Optional
from backend.cat.base import BaseRadio
from backend.config import config_manager

logger = logging.getLogger("ft991a")

# Mode mapping for FT-991A MD0 command
MODE_MAP = {
    "1": "LSB",
    "2": "USB",
    "3": "CW-U",
    "4": "FM",
    "5": "AM",
    "6": "RTTY-L",
    "7": "CW-L",
    "8": "DATA-LSB",
    "9": "RTTY-U",
    "A": "DATA-FM",
    "B": "FM-N",
    "C": "DATA-USB",
    "D": "AM-N",
    "E": "C4FM",
}


# Reverse mode mapping
REVERSE_MODE_MAP = {v: k for k, v in MODE_MAP.items()}


def raw_smeter_to_label(raw: int) -> str:
    """Convert raw 0-255 S-meter reading to standard amateur radio S-unit."""
    if raw < 15:
        return "S0"
    elif raw < 35:
        return "S1"
    elif raw < 55:
        return "S2"
    elif raw < 75:
        return "S3"
    elif raw < 95:
        return "S4"
    elif raw < 115:
        return "S5"
    elif raw < 135:
        return "S6"
    elif raw < 155:
        return "S7"
    elif raw < 175:
        return "S8"
    elif raw < 200:
        return "S9"
    elif raw < 220:
        return "+10dB"
    elif raw < 235:
        return "+20dB"
    elif raw < 250:
        return "+40dB"
    else:
        return "+60dB"


def format_frequency(hz: int) -> str:
    """Format frequency in Hz to friendly MHz representation."""
    if hz <= 0:
        return "--.---.--- MHz"
    mhz = hz / 1_000_000.0
    return f"{mhz:10.5f} MHz"


class FT991ARadio(BaseRadio):
    def __init__(self):
        cfg = config_manager.get()
        self.serial_conn: Optional[serial.Serial] = None
        self.lock = threading.Lock()
        self.ptt_active = False
        self.tx_start_time = 0.0

        # Cached telemetry
        self.current_smeter_raw = 0
        self.current_freq_hz = cfg.current_frequency_hz if cfg.current_frequency_hz else 14200000
        self.current_mode = cfg.current_mode if cfg.current_mode else "USB"
        self.current_power_watts = 50
        self.last_poll_time = 0.0

        # Repeater Offset Configuration
        band = self._get_band(self.current_freq_hz)
        self.repeater_offset_mhz = cfg.vhf_offset_mhz if band == "VHF" else cfg.uhf_offset_mhz
        self.repeater_offset_enabled = cfg.repeater_offset_enabled

    @staticmethod
    def _get_band(hz: int) -> str:
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


    @staticmethod
    def list_serial_ports() -> List[Dict[str, str]]:
        """List available serial ports with descriptions."""
        ports = []
        for p in serial.tools.list_ports.comports():
            is_yaesu = "CP210" in (p.description or "") or "Silicon Labs" in (p.manufacturer or "")
            ports.append({
                "device": p.device,
                "description": p.description,
                "hwid": p.hwid,
                "recommended": is_yaesu,
            })
        return ports

    def connect(self) -> bool:
        cfg = config_manager.get()
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                return True

            port = cfg.serial_port
            baud = cfg.baud_rate

            # Auto-detection check
            if cfg.auto_serial_port:
                from backend.cat.auto_detect import auto_detect_serial_port
                detected = auto_detect_serial_port(probe=False)
                if detected:
                    port = detected

            logger.info(f"Connecting to Yaesu FT-991A on {port} @ {baud} baud (8N2)...")

            try:
                # FT-991A default CAT protocol uses 2 stop bits (8N2)
                self.serial_conn = serial.Serial(
                    port=port,
                    baudrate=baud,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_TWO,
                    timeout=0.15,
                    write_timeout=0.2,
                )
                # Flush input/output buffers
                self.serial_conn.reset_input_buffer()
                self.serial_conn.reset_output_buffer()
                logger.info(f"Successfully opened CAT port {port}")

                # Test handshake with radio ID command
                resp = self._send_command_locked("ID;")
                if resp:
                    logger.info(f"Transceiver response to ID;: {resp.strip()}")
                return True
            except Exception as e:
                logger.warning(f"Connection to CAT port {port} failed: {e}")
                # If auto_serial_port enabled, try active probing across all candidates
                if cfg.auto_serial_port:
                    from backend.cat.auto_detect import auto_detect_serial_port
                    probed_port = auto_detect_serial_port(probe=True)
                    if probed_port and probed_port != port:
                        logger.info(f"Retrying connection with probed port: {probed_port}")
                        try:
                            self.serial_conn = serial.Serial(
                                port=probed_port,
                                baudrate=baud,
                                bytesize=serial.EIGHTBITS,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_TWO,
                                timeout=0.15,
                                write_timeout=0.2,
                            )
                            self.serial_conn.reset_input_buffer()
                            self.serial_conn.reset_output_buffer()
                            logger.info(f"Successfully opened probed CAT port {probed_port}")
                            return True
                        except Exception as e2:
                            logger.error(f"Failed to connect to probed CAT port {probed_port}: {e2}")

                self.serial_conn = None
                return False

    def disconnect(self):
        with self.lock:
            if self.ptt_active:
                try:
                    self._set_ptt_locked(False)
                except Exception:
                    pass
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                except Exception:
                    pass
            self.serial_conn = None
            logger.info("Disconnected from Yaesu FT-991A CAT port.")

    def is_connected(self) -> bool:
        return bool(self.serial_conn and self.serial_conn.is_open)

    def _send_command_locked(self, cmd: str) -> str:
        """Send command and read until ';' terminator while holding lock."""
        if not self.serial_conn or not self.serial_conn.is_open:
            return ""

        if not cmd.endswith(";"):
            cmd += ";"

        try:
            self.serial_conn.write(cmd.encode("ascii"))
            resp = bytearray()
            start = time.time()
            # Read until ';' or timeout
            while (time.time() - start) < 0.2:
                b = self.serial_conn.read(1)
                if not b:
                    break
                resp.extend(b)
                if b == b";":
                    break
            return resp.decode("ascii", errors="replace")
        except Exception as e:
            logger.warning(f"CAT command '{cmd}' error: {e}")
            return ""

    def send_raw_command(self, cmd: str) -> str:
        with self.lock:
            return self._send_command_locked(cmd)

    def set_ptt(self, transmit: bool) -> bool:
        with self.lock:
            return self._set_ptt_locked(transmit)

    def set_frequency(self, freq_hz: int) -> bool:
        with self.lock:
            self.current_freq_hz = int(freq_hz)
            cfg = config_manager.get()
            band = self._get_band(self.current_freq_hz)
            if band == "VHF":
                self.repeater_offset_mhz = cfg.vhf_offset_mhz
            elif band == "UHF":
                self.repeater_offset_mhz = cfg.uhf_offset_mhz
            cmd = f"FA{self.current_freq_hz:09d};"
            resp = self._send_command_locked(cmd)
            logger.info(f"FT-991A Frequency set to {freq_hz} Hz ({format_frequency(freq_hz)}), band: {band}")
            return bool(resp or (self.serial_conn and self.serial_conn.is_open))

    def set_mode(self, mode: str) -> bool:
        with self.lock:
            mode_upper = mode.upper()
            self.current_mode = mode_upper
            code = REVERSE_MODE_MAP.get(mode_upper, "2")
            resp = self._send_command_locked(f"MD0{code};")
            logger.info(f"FT-991A Mode set to {mode_upper} (code {code})")
            return bool(resp or (self.serial_conn and self.serial_conn.is_open))

    def set_repeater_offset(self, offset_mhz: float, enabled: bool):
        with self.lock:
            self.repeater_offset_mhz = float(offset_mhz)
            self.repeater_offset_enabled = bool(enabled)
            logger.info(f"FT-991A Repeater offset configured: {offset_mhz} MHz (enabled: {enabled})")

    def get_tx_frequency(self) -> int:
        if self.repeater_offset_enabled:
            return max(100000, self.current_freq_hz + int(self.repeater_offset_mhz * 1_000_000))
        return self.current_freq_hz

    def _set_ptt_locked(self, transmit: bool) -> bool:
        cfg = config_manager.get()
        mode = cfg.ptt_mode.upper()

        if transmit:
            logger.info(f"Keying Transceiver PTT ON ({mode})...")
            # If repeater offset is enabled, shift VFO to transmit frequency before keying
            if self.repeater_offset_enabled:
                tx_freq = self.get_tx_frequency()
                if tx_freq != self.current_freq_hz:
                    logger.info(f"Repeater shift active: Setting TX frequency to {format_frequency(tx_freq)}")
                    self._send_command_locked(f"FA{tx_freq:09d};")

            if mode == "DATA_CAT":
                cmd = "TX2;"
            elif mode == "RTS" and self.serial_conn:
                self.serial_conn.rts = True
                cmd = ""
            elif mode == "DTR" and self.serial_conn:
                self.serial_conn.dtr = True
                cmd = ""
            else:
                cmd = "TX1;"

            if cmd:
                self._send_command_locked(cmd)

            self.ptt_active = True
            self.tx_start_time = time.time()
            return True
        else:
            logger.info(f"Releasing Transceiver PTT OFF ({mode})...")
            if mode == "RTS" and self.serial_conn:
                self.serial_conn.rts = False
            elif mode == "DTR" and self.serial_conn:
                self.serial_conn.dtr = False

            # Always send TX0; to ensure CAT transmitter is unkeyed
            self._send_command_locked("TX0;")

            # If repeater offset was active, restore RX frequency
            if self.repeater_offset_enabled:
                logger.info(f"Repeater shift release: Restoring RX frequency to {format_frequency(self.current_freq_hz)}")
                self._send_command_locked(f"FA{self.current_freq_hz:09d};")

            self.ptt_active = False
            self.tx_start_time = 0.0
            return True

    def poll_telemetry(self) -> Dict[str, Any]:
        """Poll S-Meter and periodic frequency/mode status."""
        cfg = config_manager.get()

        # Safety watchdog: prevent stuck transmitter
        if self.ptt_active and self.tx_start_time > 0:
            tx_elapsed = time.time() - self.tx_start_time
            if tx_elapsed > cfg.max_tx_duration_sec:
                logger.critical(
                    f"SAFETY WATCHDOG TRIPPED! PTT active for {tx_elapsed:.1f}s (max {cfg.max_tx_duration_sec}s). Force unkeying!"
                )
                self.set_ptt(False)

        now = time.time()
        with self.lock:
            # S-Meter is polled every cycle (high rate)
            sm_resp = self._send_command_locked("SM0;")
            if sm_resp.startswith("SM0") and len(sm_resp) >= 6:
                try:
                    raw_val = int(sm_resp[3:6])
                    self.current_smeter_raw = raw_val
                except ValueError:
                    pass

            # Lower rate polling for frequency, mode, and power (~every 2 seconds)
            if (now - self.last_poll_time) > 2.0:
                self.last_poll_time = now
                # Frequency FA;
                fa_resp = self._send_command_locked("FA;")
                if fa_resp.startswith("FA") and len(fa_resp) >= 11:
                    try:
                        polled_freq = int(fa_resp[2:11])
                        # Only update if not transmitting with offset
                        if not (self.ptt_active and self.repeater_offset_enabled):
                            self.current_freq_hz = polled_freq
                    except ValueError:
                        pass

                # Mode MD0;
                md_resp = self._send_command_locked("MD0;")
                if md_resp.startswith("MD0") and len(md_resp) >= 4:
                    mode_code = md_resp[3:4]
                    self.current_mode = MODE_MAP.get(mode_code, self.current_mode)

                # Power PC;
                pc_resp = self._send_command_locked("PC;")
                if pc_resp.startswith("PC") and len(pc_resp) >= 5:
                    try:
                        self.current_power_watts = int(pc_resp[2:5])
                    except ValueError:
                        pass

        band = self._get_band(self.current_freq_hz)
        tx_freq = self.get_tx_frequency()

        return {
            "s_meter": self.current_smeter_raw,
            "s_meter_level": raw_smeter_to_label(self.current_smeter_raw),
            "frequency_hz": self.current_freq_hz,
            "frequency_formatted": format_frequency(self.current_freq_hz),
            "tx_frequency_hz": tx_freq,
            "tx_frequency_formatted": format_frequency(tx_freq),
            "repeater_offset_mhz": self.repeater_offset_mhz,
            "repeater_offset_enabled": self.repeater_offset_enabled,
            "band": band,
            "mode": self.current_mode,
            "power_watts": self.current_power_watts,
            "ptt_active": self.ptt_active,
            "connected": self.is_connected(),
        }

