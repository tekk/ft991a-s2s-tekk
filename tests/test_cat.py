"""
Unit Tests for CAT Radio Controller (FT-991A and MockRadio).
Tests CAT commands, S-Meter calibration, PTT keying, and Safety Watchdog.
"""

import time
import pytest
from unittest.mock import MagicMock, patch

from backend.cat.base import BaseRadio
from backend.cat.ft991a import FT991ARadio, raw_smeter_to_label, format_frequency, MODE_MAP
from backend.cat.mock_radio import MockRadio
from backend.config import config_manager


def test_smeter_calibration_mapping():
    """Verify raw 0-255 S-meter values map correctly to standard amateur radio units."""
    test_cases = [
        (0, "S0"),
        (10, "S0"),
        (25, "S1"),
        (45, "S2"),
        (65, "S3"),
        (80, "S4"),    # Critical S4 trigger point (~80)
        (90, "S4"),
        (105, "S5"),
        (125, "S6"),
        (145, "S7"),
        (165, "S8"),
        (190, "S9"),
        (215, "+10dB"),
        (230, "+20dB"),
        (245, "+40dB"),
        (255, "+60dB"),
    ]
    for raw_val, expected_label in test_cases:
        assert raw_smeter_to_label(raw_val) == expected_label, f"Failed for raw={raw_val}"


def test_frequency_formatting():
    """Verify conversion of Hz to MHz string."""
    assert format_frequency(0) == "--.---.--- MHz"
    assert "14.20500 MHz" in format_frequency(14205000)
    assert "7.15000 MHz" in format_frequency(7150000)
    assert "144.20000 MHz" in format_frequency(144200000)
    assert "432.10000 MHz" in format_frequency(432100000)


def test_mode_mapping():
    """Verify Yaesu FT-991A mode codes."""
    assert MODE_MAP["1"] == "LSB"
    assert MODE_MAP["2"] == "USB"
    assert MODE_MAP["3"] == "CW-U"
    assert MODE_MAP["4"] == "FM"
    assert MODE_MAP["5"] == "AM"
    assert MODE_MAP["8"] == "DATA-LSB"
    assert MODE_MAP["C"] == "DATA-USB"
    assert MODE_MAP["E"] == "C4FM"


def test_mock_radio_full_lifecycle():
    """Test mock radio lifecycle, telemetry polling, and transmission simulation."""
    radio = MockRadio()
    assert radio.connect() is True
    assert radio.is_connected() is True

    # Initial idle telemetry
    t = radio.poll_telemetry()
    assert t["connected"] is True
    assert t["ptt_active"] is False
    assert t["mode"] == "USB"
    assert t["power_watts"] == 100
    assert "14.20500 MHz" in t["frequency_formatted"]
    assert t["s_meter"] < 60  # Background noise S1-S2

    # Test PTT manual keying
    radio.set_ptt(True)
    assert radio.poll_telemetry()["ptt_active"] is True
    radio.set_ptt(False)
    assert radio.poll_telemetry()["ptt_active"] is False

    # Test simulated incoming transmission
    radio.trigger_simulated_transmission(duration_sec=0.5, raw_level=150)
    t_rx = radio.poll_telemetry()
    assert t_rx["s_meter"] >= 140  # Jumped to S7
    assert t_rx["s_meter_level"] in ("S7", "S8")

    # Test raw CAT commands
    assert radio.send_raw_command("ID;") == "ID0670;"
    assert radio.send_raw_command("MD0;") == "MD02;"
    assert radio.send_raw_command("TX1;") == "TX1;"
    assert radio.poll_telemetry()["ptt_active"] is True
    assert radio.send_raw_command("TX0;") == "TX0;"
    assert radio.poll_telemetry()["ptt_active"] is False

    radio.disconnect()
    assert radio.is_connected() is False


def test_ft991a_ptt_modes():
    """Test CAT TX1, DATA_CAT TX2, and RTS/DTR PTT selection in FT991ARadio."""
    radio = FT991ARadio()
    mock_serial = MagicMock()
    mock_serial.is_open = True
    radio.serial_conn = mock_serial

    # Mode CAT (default)
    config_manager.save({"ptt_mode": "CAT"})
    radio.set_ptt(True)
    mock_serial.write.assert_called_with(b"TX1;")
    assert radio.ptt_active is True

    radio.set_ptt(False)
    mock_serial.write.assert_called_with(b"TX0;")
    assert radio.ptt_active is False

    # Mode DATA_CAT
    config_manager.save({"ptt_mode": "DATA_CAT"})
    radio.set_ptt(True)
    mock_serial.write.assert_called_with(b"TX2;")

    # Mode RTS
    config_manager.save({"ptt_mode": "RTS"})
    radio.set_ptt(True)
    assert mock_serial.rts is True

    radio.set_ptt(False)
    assert mock_serial.rts is False


def test_ft991a_safety_watchdog():
    """Verify safety watchdog forces unkeying if TX exceeds max_tx_duration_sec."""
    radio = FT991ARadio()
    mock_serial = MagicMock()
    mock_serial.is_open = True
    radio.serial_conn = mock_serial

    # Configure short watchdog of 1 second
    config_manager.save({"max_tx_duration_sec": 1})
    radio.set_ptt(True)
    assert radio.ptt_active is True

    # Artificially age the tx_start_time
    radio.tx_start_time = time.time() - 2.0  # 2 seconds ago

    # Polling telemetry should trip watchdog and unkey
    radio.poll_telemetry()
    assert radio.ptt_active is False
    mock_serial.write.assert_any_call(b"TX0;")

    # Restore default
    config_manager.save({"max_tx_duration_sec": 30})
