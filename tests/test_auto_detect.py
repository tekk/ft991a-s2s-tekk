"""
Unit tests for FT-991A CP2105 Serial Port and USB Audio CODEC Auto-Detection.
"""

from unittest.mock import patch, MagicMock
from backend.cat.auto_detect import (
    list_candidate_ports,
    probe_cat_port,
    auto_detect_serial_port,
)
from backend.audio.devices import auto_detect_audio_devices, get_audio_devices


def test_list_candidate_ports_scoring():
    mock_port_enhanced = MagicMock()
    mock_port_enhanced.device = "/dev/ttyUSB0"
    mock_port_enhanced.description = "Silicon Labs CP2105 Dual Port - Enhanced COM Port"
    mock_port_enhanced.manufacturer = "Silicon Labs"
    mock_port_enhanced.hwid = "USB VID:PID=10C4:EA70"

    mock_port_standard = MagicMock()
    mock_port_standard.device = "/dev/ttyUSB1"
    mock_port_standard.description = "Silicon Labs CP2105 Dual Port - Standard COM Port"
    mock_port_standard.manufacturer = "Silicon Labs"
    mock_port_standard.hwid = "USB VID:PID=10C4:EA70"

    mock_port_other = MagicMock()
    mock_port_other.device = "/dev/ttyS0"
    mock_port_other.description = "Standard 16550A Serial Port"
    mock_port_other.manufacturer = "PC"
    mock_port_other.hwid = "PNP0501"

    with patch("serial.tools.list_ports.comports", return_value=[mock_port_standard, mock_port_enhanced, mock_port_other]):
        candidates = list_candidate_ports()
        assert len(candidates) == 3
        # Enhanced port should rank highest
        assert candidates[0]["device"] == "/dev/ttyUSB0"
        assert candidates[0]["is_enhanced"] is True
        assert candidates[0]["score"] > candidates[1]["score"]


def test_probe_cat_port_success():
    with patch("serial.Serial") as mock_serial_cls:
        mock_instance = MagicMock()
        mock_serial_cls.return_value.__enter__.return_value = mock_instance
        # Simulate CAT response to FA;
        mock_instance.read.return_value = b"FA014200000;"

        result = probe_cat_port("/dev/ttyUSB0", baud_rate=38400)
        assert result is True
        mock_instance.write.assert_called_with(b"FA;")


def test_probe_cat_port_failure():
    with patch("serial.Serial") as mock_serial_cls:
        mock_instance = MagicMock()
        mock_serial_cls.return_value.__enter__.return_value = mock_instance
        mock_instance.read.return_value = b""

        result = probe_cat_port("/dev/ttyUSB0", baud_rate=38400)
        assert result is False


def test_auto_detect_serial_port_heuristic_fallback():
    mock_port = MagicMock()
    mock_port.device = "/dev/ttyUSB0"
    mock_port.description = "CP2105 Enhanced"
    mock_port.manufacturer = "Silicon Labs"
    mock_port.hwid = "10C4:EA70"

    with patch("serial.tools.list_ports.comports", return_value=[mock_port]), \
         patch("backend.cat.auto_detect.probe_cat_port", return_value=False):
        # Even if probing fails, heuristic should pick the highest scored port
        detected = auto_detect_serial_port(probe=False)
        assert detected == "/dev/ttyUSB0"


def test_auto_detect_audio_devices():
    fake_devices = {
        "inputs": [
            {"id": 0, "name": "Default Input", "recommended": False},
            {"id": 3, "name": "USB Audio CODEC Microphone", "recommended": True},
        ],
        "outputs": [
            {"id": 1, "name": "Default Output", "recommended": False},
            {"id": 4, "name": "USB Audio CODEC Speaker", "recommended": True},
        ]
    }
    with patch("backend.audio.devices.get_audio_devices", return_value=fake_devices):
        result = auto_detect_audio_devices()
        assert result["input_id"] == 3
        assert result["output_id"] == 4
