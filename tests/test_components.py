"""
Automated Unit and Integration Tests for Yaesu FT-991A AI S2S Bridge.
Tests CAT decoding, audio resampling, port fallback, disk manager auto-roll, and prompt security.
"""

import os
import shutil
import asyncio
import numpy as np
from pathlib import Path

from backend.port_finder import is_port_available, find_free_high_port, resolve_web_port
from backend.cat.ft991a import raw_smeter_to_label, format_frequency, MODE_MAP
from backend.cat.mock_radio import MockRadio
from backend.audio.vad import calculate_audio_levels
from backend.audio.streamer import resample_pcm16
from backend.recording.disk_manager import DiskManager
from backend.recording.recorder import AudioRecorder
from backend.openai_client.prompts import generate_system_prompt
from backend.config import config_manager


def test_port_finder():
    # Test high port discovery
    high_port = find_free_high_port()
    assert high_port > 10000, f"Expected port > 10000, got {high_port}"

    # Test resolve_web_port with an intentionally unavailable or test port
    port, was_fallback = resolve_web_port(preferred_port=80)
    assert port > 0
    print(f"[TEST PASS] Port finder resolved: port={port}, fallback={was_fallback}")


def test_cat_parser():
    # Test S-meter conversion
    assert raw_smeter_to_label(0) == "S0"
    assert raw_smeter_to_label(80) == "S4"
    assert raw_smeter_to_label(185) == "S9"
    assert raw_smeter_to_label(230) == "+20dB"
    assert raw_smeter_to_label(255) == "+60dB"

    # Test frequency formatting
    assert "14.20500 MHz" in format_frequency(14205000)
    assert "144.20000 MHz" in format_frequency(144200000)
    assert "432.10000 MHz" in format_frequency(432100000)

    # Test mode map
    assert MODE_MAP["1"] == "LSB"
    assert MODE_MAP["2"] == "USB"
    assert MODE_MAP["4"] == "FM"
    assert MODE_MAP["C"] == "DATA-USB"
    print("[TEST PASS] CAT parsing and formatting functions verified.")


def test_audio_resampling_and_levels():
    # Generate 100ms 48kHz sine wave
    duration = 0.1
    sr_48k = 48000
    t = np.linspace(0, duration, int(sr_48k * duration), endpoint=False)
    sine = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    pcm_48k = sine.tobytes()

    # Calculate levels
    rms, peak = calculate_audio_levels(pcm_48k)
    assert rms > 20.0, f"Expected non-zero RMS, got {rms}"
    assert peak > 30.0, f"Expected non-zero Peak, got {peak}"

    # Resample 48k -> 24k
    pcm_24k = resample_pcm16(pcm_48k, from_rate=48000, to_rate=24000)
    expected_len = int(len(pcm_48k) / 2)
    # Length should match half within small tolerance due to filter edge
    assert abs(len(pcm_24k) - expected_len) <= 4, f"Resampled len mismatch: {len(pcm_24k)} vs {expected_len}"
    print("[TEST PASS] Audio metering and 48kHz -> 24kHz resampling verified.")


def test_prompt_guardrails():
    prompt = generate_system_prompt(callsign="W1AW", custom_instructions="Repeater test")
    assert "W1AW" in prompt
    assert "MAXIMUM 1 TO 3 SENTENCES" in prompt
    assert "ANTI-PROMPT-INJECTION" in prompt
    assert "ignore all previous instructions" in prompt.lower()
    print("[TEST PASS] Ham persona and anti-prompt-injection security prompt verified.")


async def test_disk_manager_auto_roll():
    test_dir = Path("/tmp/ft991a_test_recordings")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)

    try:
        dm = DiskManager(directory=test_dir)
        stats = dm.get_storage_stats()
        assert stats["total_mb"] > 0

        # Create dummy audio recordings with artificial timestamps
        file1 = test_dir / "rx_20260101_000001_oldest.opus"
        file2 = test_dir / "tx_20260101_000002_newest.opus"

        file1.write_bytes(b"0" * (1024 * 1024 * 5))  # 5 MB
        file2.write_bytes(b"0" * (1024 * 1024 * 5))  # 5 MB

        os.utime(file1, (1000, 1000))
        os.utime(file2, (2000, 2000))

        # Force a small threshold to trigger auto-roll
        cfg = config_manager.get()
        orig_max = cfg.max_recordings_mb
        config_manager.save({"max_recordings_mb": 6})  # Total is 10MB, limit 6MB

        result = dm.check_and_auto_roll()
        assert result["purged"] is True
        assert result["deleted_count"] >= 1
        # Oldest file1 should be deleted, newest file2 preserved
        assert not file1.exists()
        assert file2.exists()

        # Restore config
        config_manager.save({"max_recordings_mb": orig_max})
        print(f"[TEST PASS] Storage auto-roll purged {result['deleted_count']} oldest files (reclaimed {result['reclaimed_mb']}MB).")
    finally:
        shutil.rmtree(test_dir)


async def test_audio_recorder():
    rec = AudioRecorder(directory=Path("/tmp/ft991a_test_rec_out"))
    # Generate 0.5s 24kHz PCM16 audio
    samples = (0.3 * np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, 12000)) * 32767).astype(np.int16)
    pcm = samples.tobytes()

    # Test encoding to OPUS
    info_opus = await rec.save_recording(pcm, sample_rate=24000, channels=1, prefix="rx", custom_format="opus")
    assert info_opus is not None
    assert Path(info_opus["path"]).exists()
    assert info_opus["size_bytes"] > 0
    print(f"[TEST PASS] Encoded OPUS file: {info_opus['filename']} ({info_opus['size_bytes']} bytes)")

    # Test encoding to MP3
    info_mp3 = await rec.save_recording(pcm, sample_rate=24000, channels=1, prefix="tx", custom_format="mp3")
    assert info_mp3 is not None
    assert Path(info_mp3["path"]).exists()
    print(f"[TEST PASS] Encoded MP3 file: {info_mp3['filename']} ({info_mp3['size_bytes']} bytes)")

    shutil.rmtree(Path("/tmp/ft991a_test_rec_out"))


def test_mock_radio():
    radio = MockRadio()
    assert radio.connect() is True
    assert radio.is_connected() is True

    telemetry = radio.poll_telemetry()
    assert telemetry["s_meter"] >= 0
    assert "14.20500 MHz" in telemetry["frequency_formatted"]
    assert telemetry["mode"] == "USB"

    # Trigger transmission
    radio.trigger_simulated_transmission(duration_sec=1.0, raw_level=140)
    t_rx = radio.poll_telemetry()
    assert t_rx["s_meter"] >= 130, f"Expected S-meter to jump, got {t_rx['s_meter']}"

    # Test PTT keying
    radio.set_ptt(True)
    assert radio.poll_telemetry()["ptt_active"] is True
    radio.set_ptt(False)
    assert radio.poll_telemetry()["ptt_active"] is False
    print("[TEST PASS] MockRadio hardware simulation validated.")


if __name__ == "__main__":
    test_port_finder()
    test_cat_parser()
    test_audio_resampling_and_levels()
    test_prompt_guardrails()
    test_mock_radio()
    asyncio.run(test_disk_manager_auto_roll())
    asyncio.run(test_audio_recorder())
    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
