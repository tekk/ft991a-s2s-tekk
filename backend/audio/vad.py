"""
Audio Metering, RMS, Peak, and Voice Activity Detection (VAD) utilities.
"""

import math
import numpy as np
from typing import Tuple

def calculate_audio_levels(pcm16_bytes: bytes) -> Tuple[float, float]:
    """
    Given raw 16-bit linear PCM audio bytes:
    Returns (rms_pct, peak_pct) where values are normalized 0.0 to 100.0.
    """
    if not pcm16_bytes or len(pcm16_bytes) < 2:
        return 0.0, 0.0

    try:
        # Load as int16
        samples = np.frombuffer(pcm16_bytes, dtype=np.int16).astype(np.float32)
        if len(samples) == 0:
            return 0.0, 0.0

        # Peak amplitude (0.0 to 1.0)
        peak = np.max(np.abs(samples)) / 32768.0
        peak_pct = min(100.0, round(float(peak * 100.0), 1))

        # Root Mean Square
        rms = np.sqrt(np.mean(samples ** 2)) / 32768.0
        # Convert to a human-friendly perceptual logarithmic scale
        if rms > 1e-5:
            db = 20 * math.log10(rms)
            # Map -60 dBFS .. 0 dBFS to 0% .. 100%
            rms_pct = min(100.0, max(0.0, (db + 60.0) * (100.0 / 60.0)))
        else:
            rms_pct = 0.0

        return round(float(rms_pct), 1), peak_pct
    except Exception:
        return 0.0, 0.0
