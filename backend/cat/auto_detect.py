"""
Automatic Serial Port Discovery and Verification for Yaesu FT-991A.
Identifies Silicon Labs CP2105 USB-to-UART bridges, probes candidate ports with CAT queries,
and persists verified preferences.
"""

import time
import logging
from typing import Optional, List, Dict, Tuple
import serial
import serial.tools.list_ports

from backend.config import config_manager

logger = logging.getLogger("cat_autodetect")

# Known USB VID:PID for FT-991A and amateur radio serial interfaces
YAESU_CP2105_VID_PID = [
    (0x10C4, 0xEA70),  # Silicon Labs CP2105 Dual Port (Standard FT-991A)
    (0x10C4, 0xEA60),  # Silicon Labs CP2102 Single Port
    (0x0403, 0x6001),  # FTDI FT232R
    (0x0403, 0x6015),  # FTDI FT230X
    (0x1A86, 0x7523),  # CH340
]


def list_candidate_ports() -> List[Dict[str, Any]]:
    """List and score all available host serial ports for FT-991A suitability."""
    candidates = []
    for p in serial.tools.list_ports.comports():
        score = 0
        desc = (p.description or "").lower()
        mfg = (p.manufacturer or "").lower()
        hwid = (p.hwid or "").lower()

        # Score CP2105 / FT-991A signatures
        if "enhanced" in desc:
            score += 50  # Enhanced COM port is the CAT control port
        if "cp210" in desc or "cp210" in hwid or "silicon labs" in mfg:
            score += 30
        if "ft991" in desc or "yaesu" in desc:
            score += 40
        if "standard" in desc:
            score += 10  # Standard port is usually audio/data handshake

        for vid, pid in YAESU_CP2105_VID_PID:
            if f"{vid:04x}:{pid:04x}".lower() in hwid:
                score += 25
                break

        candidates.append({
            "device": p.device,
            "description": p.description,
            "hwid": p.hwid,
            "score": score,
            "is_enhanced": "enhanced" in desc,
        })

    # Sort descending by score
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates


def probe_cat_port(port_device: str, baud_rate: int = 38400, timeout: float = 0.3) -> bool:
    """Send a harmless CAT read command (FA; or IF;) to check if transceiver responds."""
    try:
        with serial.Serial(
            port=port_device,
            baudrate=baud_rate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=timeout,
            write_timeout=timeout,
        ) as s:
            # Clear buffers
            s.reset_input_buffer()
            s.reset_output_buffer()

            # Query VFO-A frequency
            s.write(b"FA;")
            s.flush()
            time.sleep(0.08)

            resp = s.read(30)
            if b"FA" in resp:
                logger.info(f"Port {port_device} verified active FT-991A CAT (responded: {resp.strip()})")
                return True

            # Try IF; (Transceiver Information)
            s.write(b"IF;")
            s.flush()
            time.sleep(0.08)
            resp2 = s.read(40)
            if b"IF" in resp2:
                logger.info(f"Port {port_device} verified active FT-991A CAT via IF; ({resp2.strip()})")
                return True

    except Exception as e:
        logger.debug(f"Probing {port_device} failed: {e}")

    return False


def auto_detect_serial_port(probe: bool = True) -> Optional[str]:
    """
    Intelligently discover and select the FT-991A CAT serial port.
    Checks:
    1. User preferred port (if explicitly set and responsive)
    2. Candidate ports sorted by CP2105 Enhanced heuristics
    3. Active CAT protocol probe verification (FA;/IF;)
    4. Automatically updates and persists config preference if changed.
    """
    cfg = config_manager.get()
    baud = cfg.baud_rate

    # 1. Check if configured port is already valid
    current_port = cfg.serial_port
    if probe and current_port and probe_cat_port(current_port, baud_rate=baud):
        return current_port

    candidates = list_candidate_ports()
    if not candidates:
        logger.warning("No serial ports found on system.")
        return current_port

    # 2. Try preferred port if set
    if cfg.preferred_serial_port:
        for c in candidates:
            if c["device"] == cfg.preferred_serial_port:
                if not probe or probe_cat_port(c["device"], baud_rate=baud):
                    logger.info(f"Auto-selected preferred serial port: {c['device']}")
                    return c["device"]

    # 3. Probe candidates in scored order
    if probe:
        for c in candidates:
            if probe_cat_port(c["device"], baud_rate=baud):
                selected = c["device"]
                logger.info(f"Auto-detected verified FT-991A CAT port: {selected}")
                if selected != current_port:
                    config_manager.save({"serial_port": selected, "preferred_serial_port": selected})
                return selected

    # 4. Fallback: pick highest scored candidate (e.g. Enhanced COM port)
    best = candidates[0]
    selected = best["device"]
    logger.info(f"Auto-selected candidate port by heuristic: {selected} ({best['description']})")
    if selected != current_port:
        config_manager.save({"serial_port": selected})
    return selected
