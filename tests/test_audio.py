"""
Unit Tests for Audio Pipeline (Resampling, Metering, and Streamer).
"""

import time
import math
import numpy as np
import pytest

from backend.audio.vad import calculate_audio_levels
from backend.audio.streamer import resample_pcm16, AudioStreamer, OPENAI_SAMPLE_RATE
from backend.audio.devices import resolve_device_index, get_audio_devices
from backend.config import config_manager


def test_audio_level_calculations():
    """Test RMS and Peak volume calculations for silence, tones, and full scale."""
    # 1. Complete Silence
    silence = np.zeros(1000, dtype=np.int16).tobytes()
    rms_silence, peak_silence = calculate_audio_levels(silence)
    assert rms_silence == 0.0
    assert peak_silence == 0.0

    # 2. 440 Hz Sine Tone at half scale (~ -6 dBFS)
    duration = 0.1
    sr = 24000
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    tone_half = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16).tobytes()
    rms_tone, peak_tone = calculate_audio_levels(tone_half)
    assert 45.0 <= peak_tone <= 55.0
    assert rms_tone > 25.0

    # 3. Full scale square wave (100% peak, 100% RMS)
    square_full = (np.ones(1000, dtype=np.int16) * 32767).tobytes()
    rms_full, peak_full = calculate_audio_levels(square_full)
    assert peak_full == 100.0
    assert rms_full >= 98.0


def test_resampling_rates():
    """Test resampling fidelity across common audio hardware rates."""
    sr_list = [48000, 44100, 16000]
    target_sr = OPENAI_SAMPLE_RATE  # 24000 Hz

    for from_sr in sr_list:
        duration = 0.2  # 200 ms
        t = np.linspace(0, duration, int(from_sr * duration), endpoint=False)
        tone = (0.4 * np.sin(2 * np.pi * 1000 * t) * 32767).astype(np.int16).tobytes()

        resampled = resample_pcm16(tone, from_rate=from_sr, to_rate=target_sr)
        expected_samples = int(duration * target_sr)
        actual_samples = len(resampled) // 2

        # Verify length within 4 samples tolerance
        assert abs(actual_samples - expected_samples) <= 4, (
            f"Rate {from_sr}->{target_sr} sample mismatch: got {actual_samples}, expected {expected_samples}"
        )

        # Verify resampled audio maintains signal energy
        rms, peak = calculate_audio_levels(resampled)
        assert peak > 20.0
        assert rms > 20.0


def test_stereo_to_mono_resampling():
    """Test stereo channel downmixing to mono."""
    samples_per_chan = 1000
    # Left channel = 10000, Right channel = 20000
    left = np.full(samples_per_chan, 10000, dtype=np.int16)
    right = np.full(samples_per_chan, 20000, dtype=np.int16)
    stereo = np.empty((samples_per_chan, 2), dtype=np.int16)
    stereo[:, 0] = left
    stereo[:, 1] = right

    mono_bytes = resample_pcm16(
        stereo.tobytes(),
        from_rate=24000,
        to_rate=24000,
        from_channels=2,
        to_channels=1,
    )
    mono_samples = np.frombuffer(mono_bytes, dtype=np.int16)
    assert len(mono_samples) == samples_per_chan
    # Average of 10000 and 20000 is 15000
    assert abs(mono_samples[0] - 15000) <= 2


def test_audio_streamer_virtual_mode():
    """Test AudioStreamer virtual loop and queue draining."""
    config_manager.save({"simulated_mode": True})
    streamer = AudioStreamer()

    received_chunks = []
    def on_rx(chunk):
        received_chunks.append(chunk)

    streamer.start(on_rx_chunk=on_rx)
    streamer.set_capturing(True)

    time.sleep(0.2)
    assert len(received_chunks) > 0, "Expected virtual audio chunks during capture"

    streamer.set_capturing(False)

    # Test TX queue
    dummy_tx_pcm = (np.ones(2400, dtype=np.int16) * 1000).tobytes()  # 100ms
    streamer.enqueue_tx_audio(dummy_tx_pcm)
    assert streamer.is_playback_finished() is False

    # Wait for queue to drain in simulation
    time.sleep(0.3)
    assert streamer.is_playback_finished() is True

    streamer.stop()
