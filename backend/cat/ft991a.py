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
        self.serial_conn: Optional[serial.Serial] = None
        self.lock = threading.Lock()
        self.ptt_active = False
        self.tx_start_time = 0.0

        # Cached telemetry
        self.current_smeter_raw = 0
        self.current_freq_hz = 14200000
        self.current_mode = "USB"
        self.current_power_watts = 50
        self.last_poll_time = 0.0

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
                logger.error(f"Failed to connect to CAT port {port}: {e}")
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

    def _set_ptt_locked(self, transmit: bool) -> bool:
        cfg = config_manager.get()
        mode = cfg.ptt_mode.upper()

        if transmit:
            logger.info(f"Keying Transceiver PTT ON ({mode})...")
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
                        self.current_freq_hz = int(fa_resp[2:11])
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

        return {
            "s_meter": self.current_smeter_raw,
            "s_meter_level": raw_smeter_to_label(self.current_smeter_raw),
            "frequency_hz": self.current_freq_hz,
            "frequency_formatted": format_frequency(self.current_freq_hz),
            "mode": self.current_mode,
            "power_watts": self.current_power_watts,
            "ptt_active": self.ptt_active,
            "connected": self.is_connected(),
        }
