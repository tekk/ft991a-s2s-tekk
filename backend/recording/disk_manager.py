"""
Disk Space Monitor and FIFO Rolling Storage Purger for SBCs.
Ensures SD cards and eMMC storage never exhaust free space due to audio archives.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from backend.config import RECORDINGS_DIR, config_manager

logger = logging.getLogger("disk_manager")

class DiskManager:
    def __init__(self, directory: Path = RECORDINGS_DIR):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def get_storage_stats(self) -> Dict[str, Any]:
        """Return disk metrics in Megabytes."""
        try:
            usage = shutil.disk_usage(self.directory)
            total_mb = round(usage.total / (1024 * 1024), 1)
            free_mb = round(usage.free / (1024 * 1024), 1)
            used_mb = round(usage.used / (1024 * 1024), 1)
            percent_used = round((usage.used / usage.total) * 100, 1)
        except Exception as e:
            logger.error(f"Error checking disk usage: {e}")
            total_mb, free_mb, used_mb, percent_used = 0, 0, 0, 0

        # Calculate recordings folder metrics
        rec_size_bytes = 0
        file_count = 0
        for entry in self.directory.iterdir():
            if entry.is_file() and entry.suffix.lower() in (".opus", ".mp3", ".ogg", ".m4a", ".wav"):
                try:
                    rec_size_bytes += entry.stat().st_size
                    file_count += 1
                except Exception:
                    pass

        recordings_mb = round(rec_size_bytes / (1024 * 1024), 2)

        return {
            "total_mb": total_mb,
            "free_mb": free_mb,
            "used_mb": used_mb,
            "percent_used": percent_used,
            "recordings_mb": recordings_mb,
            "recordings_count": file_count,
            "min_free_threshold_mb": config_manager.get().min_free_disk_mb,
            "max_recordings_threshold_mb": config_manager.get().max_recordings_mb,
        }

    def check_and_auto_roll(self) -> Dict[str, Any]:
        """
        Check if storage is low or recordings exceed limit.
        If so, delete oldest recordings (FIFO) until disk health is restored.
        """
        cfg = config_manager.get()
        stats = self.get_storage_stats()
        min_free = cfg.min_free_disk_mb
        max_rec = cfg.max_recordings_mb

        needs_purge = False
        reasons = []

        if stats["free_mb"] < min_free:
            needs_purge = True
            reasons.append(f"Free disk ({stats['free_mb']}MB) is below minimum threshold ({min_free}MB)")

        if stats["recordings_mb"] > max_rec:
            needs_purge = True
            reasons.append(f"Recordings size ({stats['recordings_mb']}MB) exceeds maximum allocation ({max_rec}MB)")

        if not needs_purge:
            return {"purged": False, "deleted_count": 0, "reclaimed_mb": 0.0}

        logger.warning(f"Storage limit reached: {', '.join(reasons)}. Rolling old recordings...")

        # Gather files sorted by modification time (oldest first)
        audio_files: List[Tuple[Path, float, int]] = []
        for entry in self.directory.iterdir():
            if entry.is_file() and entry.suffix.lower() in (".opus", ".mp3", ".ogg", ".m4a", ".wav"):
                try:
                    stat = entry.stat()
                    audio_files.append((entry, stat.st_mtime, stat.st_size))
                except Exception:
                    pass

        audio_files.sort(key=lambda x: x[1])

        deleted_count = 0
        reclaimed_bytes = 0

        # Purge files until free space is at least min_free + 100MB and recordings_mb <= max_rec * 0.9
        target_free = min_free + 100
        target_rec = max_rec * 0.9

        for path, _, size in audio_files:
            try:
                path.unlink()
                deleted_count += 1
                reclaimed_bytes += size
            except Exception as e:
                logger.error(f"Failed to delete old recording {path}: {e}")

            # Re-check usage
            current_stats = self.get_storage_stats()
            if current_stats["free_mb"] >= target_free and current_stats["recordings_mb"] <= target_rec:
                break

        reclaimed_mb = round(reclaimed_bytes / (1024 * 1024), 2)
        logger.info(f"Storage auto-roll complete: Purged {deleted_count} files, reclaimed {reclaimed_mb} MB")

        return {
            "purged": True,
            "deleted_count": deleted_count,
            "reclaimed_mb": reclaimed_mb,
            "stats_after": self.get_storage_stats(),
        }


disk_manager = DiskManager()
