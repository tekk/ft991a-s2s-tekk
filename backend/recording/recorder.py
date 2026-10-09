"""
Asynchronous Audio Recorder and Compressor.
Encodes raw PCM audio streams into M4A, MP3, OGG, or OPUS using ffmpeg.
Triggers disk_manager auto-roll on completion.
"""

import os
import time
import uuid
import wave
import json
import shutil
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from backend.config import RECORDINGS_DIR, DATA_DIR, AUDIO_QUALITY_PRESETS, config_manager
from backend.recording.disk_manager import disk_manager

logger = logging.getLogger("recorder")
RECORDINGS_META_FILE = DATA_DIR / "recordings_metadata.json"


class AudioRecorder:
    def __init__(self, directory: Path = RECORDINGS_DIR):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_available = shutil.which("ffmpeg") is not None
        self._current_playback_proc: Optional[subprocess.Popen] = None
        if not self.ffmpeg_available:
            logger.warning("ffmpeg is not installed. Will fallback to uncompressed WAV until ffmpeg is available.")
        self.metadata_catalog = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load persistent recordings metadata index from JSON."""
        if RECORDINGS_META_FILE.exists():
            try:
                with open(RECORDINGS_META_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading recordings metadata: {e}")
        return {}

    def _save_metadata(self):
        """Persist recordings metadata index to disk."""
        try:
            with open(RECORDINGS_META_FILE, "w", encoding="utf-8") as f:
                json.dump(self.metadata_catalog, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save recordings metadata: {e}")


    async def save_recording(
        self,
        pcm_bytes: bytes,
        sample_rate: int = 24000,
        channels: int = 1,
        prefix: str = "rx",
        custom_format: Optional[str] = None,
        custom_preset: Optional[str] = None,
        transcript: str = "",
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

        # Determine effective bitrate from preset
        preset_key = (custom_preset or cfg.recording_preset).lower()
        preset_info = AUDIO_QUALITY_PRESETS.get(preset_key, AUDIO_QUALITY_PRESETS["standard"])
        bitrate = preset_info.get("bitrates_by_format", {}).get(fmt, cfg.recording_bitrate)
        if not bitrate or bitrate == "none":
            bitrate = cfg.recording_bitrate or "32k"

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
                    bitrate=bitrate,
                )

            file_size_bytes = target_path.stat().st_size
            logger.info(f"Saved {prefix.upper()} audio: {filename} ({duration_sec:.1f}s, {file_size_bytes // 1024} KB, {bitrate})")

            # Run disk watchdog after write
            disk_manager.check_and_auto_roll()

            rec_data = {
                "id": filename,
                "filename": filename,
                "path": str(target_path),
                "url": f"/recordings/{filename}",
                "format": fmt,
                "preset": preset_key,
                "bitrate": bitrate,
                "duration_seconds": round(duration_sec, 2),
                "duration": round(duration_sec, 2),
                "size_bytes": file_size_bytes,
                "prefix": prefix,
                "type": prefix.upper(),
                "created_at": time.time(),
                "timestamp": time.time(),
                "transcript": transcript,
            }

            self.metadata_catalog[filename] = rec_data
            self._save_metadata()

            return rec_data
        except Exception as e:
            logger.error(f"Failed to encode/save audio recording: {e}", exc_info=True)
            return None

    def list_recordings(
        self,
        filter_type: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return list of historical recordings sorted newest first."""
        # 1. Ensure any files on disk without metadata are populated
        try:
            for entry in self.directory.iterdir():
                if entry.is_file() and entry.suffix.lower() in (".opus", ".mp3", ".ogg", ".m4a", ".wav"):
                    if entry.name not in self.metadata_catalog:
                        stat = entry.stat()
                        prefix = "rx" if entry.name.startswith("rx_") else ("tx" if entry.name.startswith("tx_") else "rec")
                        fmt = entry.suffix.lower().lstrip(".")
                        self.metadata_catalog[entry.name] = {
                            "id": entry.name,
                            "filename": entry.name,
                            "path": str(entry),
                            "url": f"/recordings/{entry.name}",
                            "format": fmt,
                            "preset": "standard",
                            "bitrate": "32k",
                            "duration_seconds": 0.0,
                            "duration": 0.0,
                            "size_bytes": stat.st_size,
                            "prefix": prefix,
                            "type": prefix.upper(),
                            "created_at": stat.st_mtime,
                            "timestamp": stat.st_mtime,
                            "transcript": "",
                        }
        except Exception as e:
            logger.warning(f"Error scanning recordings directory: {e}")

        # 2. Filter and sort
        items = list(self.metadata_catalog.values())

        # Clean out any entries whose files were deleted
        valid_items = []
        for it in items:
            p = self.directory / it["filename"]
            if p.exists():
                valid_items.append(it)
        if len(valid_items) != len(items):
            self.metadata_catalog = {it["filename"]: it for it in valid_items}
            self._save_metadata()

        if filter_type:
            ft = filter_type.upper()
            valid_items = [it for it in valid_items if it.get("type") == ft]

        if search:
            s_lower = search.lower()
            valid_items = [
                it for it in valid_items
                if s_lower in it.get("transcript", "").lower() or s_lower in it.get("filename", "").lower()
            ]

        # Sort newest first
        valid_items.sort(key=lambda x: x.get("timestamp", x.get("created_at", 0)), reverse=True)

        return valid_items[offset : offset + limit]

    def delete_recording(self, filename: str) -> bool:
        """Delete recording file and its metadata index entry."""
        target_path = self.directory / filename
        removed = False
        if target_path.exists():
            try:
                target_path.unlink()
                removed = True
            except Exception as e:
                logger.error(f"Failed to delete recording {filename}: {e}")
                return False
        if filename in self.metadata_catalog:
            del self.metadata_catalog[filename]
            self._save_metadata()
            removed = True
        disk_manager.check_and_auto_roll()
        return removed

    def play_recording_locally(self, filename: str) -> bool:
        """Play recording on local host audio output using ffplay or aplay."""
        target_path = self.directory / filename
        if not target_path.exists():
            return False

        self.stop_local_playback()

        try:
            if shutil.which("ffplay"):
                cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(target_path)]
                self._current_playback_proc = subprocess.Popen(cmd)
                return True
            elif target_path.suffix.lower() == ".wav" and shutil.which("aplay"):
                cmd = ["aplay", "-q", str(target_path)]
                self._current_playback_proc = subprocess.Popen(cmd)
                return True
        except Exception as e:
            logger.error(f"Local audio playback failed: {e}")
        return False

    def stop_local_playback(self):
        """Stop active local playback process."""
        if self._current_playback_proc and self._current_playback_proc.poll() is None:
            try:
                self._current_playback_proc.terminate()
            except Exception:
                pass
            self._current_playback_proc = None

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

