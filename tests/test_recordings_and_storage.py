"""
Unit Tests for Audio Recording Encoders (M4A, MP3, OGG, OPUS) and Disk Auto-Roll Watchdog.
"""

import os
import shutil
import asyncio
import numpy as np
import pytest
from pathlib import Path

from backend.recording.recorder import AudioRecorder
from backend.recording.disk_manager import DiskManager
from backend.config import config_manager


@pytest.fixture
def temp_recordings_dir():
    test_dir = Path("/tmp/ft991a_test_rec_suite")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)
    yield test_dir
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.mark.asyncio
async def test_audio_recorder_all_codecs(temp_recordings_dir):
    """Verify recording and compression across OPUS, MP3, OGG, M4A, and WAV."""
    recorder = AudioRecorder(directory=temp_recordings_dir)

    # Generate 0.3s of 24kHz test audio
    duration = 0.3
    sr = 24000
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    pcm_bytes = (0.4 * np.sin(2 * np.pi * 500 * t) * 32767).astype(np.int16).tobytes()

    formats = ["opus", "mp3", "ogg", "m4a", "wav"]
    for fmt in formats:
        rec_info = await recorder.save_recording(
            pcm_bytes=pcm_bytes,
            sample_rate=sr,
            channels=1,
            prefix=f"test_{fmt}",
            custom_format=fmt,
        )
        assert rec_info is not None, f"Failed to save format {fmt}"
        assert rec_info["format"] == fmt
        assert rec_info["duration_seconds"] == pytest.approx(0.3, 0.05)
        assert Path(rec_info["path"]).exists()
        assert rec_info["size_bytes"] > 0
        assert rec_info["url"].startswith("/recordings/")


def test_disk_manager_fifo_purge(temp_recordings_dir):
    """Verify FIFO rolling deletion purges oldest files and preserves newer ones."""
    dm = DiskManager(directory=temp_recordings_dir)

    # Create 4 dummy recordings with staggered mtimes
    files = []
    for i in range(4):
        f = temp_recordings_dir / f"rx_20260916_00000{i}.opus"
        f.write_bytes(b"x" * (1024 * 1024 * 2))  # 2 MB each
        os.utime(f, (1000 + i * 100, 1000 + i * 100))
        files.append(f)

    # Current total is 8MB
    stats_before = dm.get_storage_stats()
    assert stats_before["recordings_count"] == 4
    assert stats_before["recordings_mb"] >= 7.9

    # Configure max recordings limit to 4 MB to trigger auto-roll
    orig_max = config_manager.get().max_recordings_mb
    config_manager.save({"max_recordings_mb": 4})

    result = dm.check_and_auto_roll()
    assert result["purged"] is True
    assert result["deleted_count"] >= 2

    # Verify oldest files were deleted and newest survived
    assert not files[0].exists(), "Oldest file was not purged"
    assert not files[1].exists(), "Second oldest file was not purged"
    assert files[3].exists(), "Newest file was mistakenly deleted"

    # Restore config
    config_manager.save({"max_recordings_mb": orig_max})
