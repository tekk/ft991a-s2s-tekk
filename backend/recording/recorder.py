"""
Asynchronous Audio Recorder and Compressor.
Encodes raw PCM audio streams into M4A, MP3, OGG, or OPUS using ffmpeg.
Triggers disk_manager auto-roll on completion.
"""

import os
import time
import uuid
import wave
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from backend.config import RECORDINGS_DIR, config_manager
from backend.recording.disk_manager import disk_manager

logger = logging.getLogger("recorder")

class AudioRecorder:
    def __init__(self, directory: Path = RECORDINGS_DIR):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_available = shutil.which("ffmpeg") is not None
        if not self.ffmpeg_available:
            logger.warning("ffmpeg is not installed. Will fallback to uncompressed WAV until ffmpeg is available.")

    async def save_recording(
        self,
        pcm_bytes: bytes,
        sample_rate: int = 24000,
        channels: int = 1,
        prefix: str = "rx",
        custom_format: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Save raw PCM16 audio bytes to compressed format asynchronously.
        Returns dict with file metadata (filename, duration, size, url).
        """
        cfg = config_manager.get()
        if not cfg.recordings_enabled or len(pcm_bytes) == 0:
            return None

        # Check storage space before writing
        disk_manager.check_and_auto_roll()

        fmt = (custom_format or cfg.recording_format).lower()
        valid_formats = ["opus", "mp3", "ogg", "m4a", "wav"]
        if fmt not in valid_formats:
            fmt = "opus"

        # If ffmpeg is missing and not wav, fallback to wav
        if not self.ffmpeg_available and fmt != "wav":
            logger.warning(f"ffmpeg not found, falling back from {fmt} to wav")
            fmt = "wav"

        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        filename = f"{prefix}_{timestamp_str}_{unique_id}.{fmt}"
        target_path = self.directory / filename

        duration_sec = len(pcm_bytes) / (sample_rate * channels * 2)

        try:
            if fmt == "wav":
                await self._write_wav_async(target_path, pcm_bytes, sample_rate, channels)
            else:
                await self._encode_with_ffmpeg(
                    pcm_bytes=pcm_bytes,
                    sample_rate=sample_rate,
                    channels=channels,
                    output_path=target_path,
                    fmt=fmt,
                    bitrate=cfg.recording_bitrate,
                )

            file_size_bytes = target_path.stat().st_size
            logger.info(f"Saved {prefix.upper()} audio: {filename} ({duration_sec:.1f}s, {file_size_bytes // 1024} KB)")

            # Run disk watchdog after write
            disk_manager.check_and_auto_roll()

            return {
                "filename": filename,
                "path": str(target_path),
                "url": f"/recordings/{filename}",
                "format": fmt,
                "duration_seconds": round(duration_sec, 2),
                "size_bytes": file_size_bytes,
                "prefix": prefix,
                "created_at": time.time(),
            }
        except Exception as e:
            logger.error(f"Failed to encode/save audio recording: {e}", exc_info=True)
            return None

    async def _write_wav_async(self, target_path: Path, pcm_bytes: bytes, sample_rate: int, channels: int):
        loop = asyncio.get_running_loop()
        def write_wav():
            with wave.open(str(target_path), "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_bytes)
        await loop.run_in_executor(None, write_wav)

    async def _encode_with_ffmpeg(
        self,
        pcm_bytes: bytes,
        sample_rate: int,
        channels: int,
        output_path: Path,
        fmt: str,
        bitrate: str = "32k",
    ):
        """Pipe raw PCM into ffmpeg and compress to target format."""
        # Setup codec parameters based on format
        codec_args = []
        if fmt == "opus":
            codec_args = ["-c:a", "libopus", "-b:a", bitrate, "-vbr", "on"]
        elif fmt == "mp3":
            codec_args = ["-c:a", "libmp3lame", "-b:a", bitrate]
        elif fmt == "ogg":
            codec_args = ["-c:a", "libvorbis", "-b:a", bitrate]
        elif fmt == "m4a":
            codec_args = ["-c:a", "aac", "-b:a", bitrate]
        else:
            codec_args = ["-c:a", "copy"]

        cmd = [
            "ffmpeg",
            "-y",                     # Overwrite output without asking
            "-f", "s16le",            # Raw 16-bit signed PCM input
            "-ar", str(sample_rate),  # Sample rate
            "-ac", str(channels),     # Channels
            "-i", "pipe:0",           # Read from stdin
            *codec_args,
            str(output_path),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate(input=pcm_bytes)

        if proc.returncode != 0:
            err_msg = stderr.decode(errors="replace")
            logger.error(f"ffmpeg error (exit {proc.returncode}): {err_msg}")
            # Fallback: if encoder failed, save as WAV so we don't lose the recording
            wav_path = output_path.with_suffix(".wav")
            await self._write_wav_async(wav_path, pcm_bytes, sample_rate, channels)


audio_recorder = AudioRecorder()
