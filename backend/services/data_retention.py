"""
Ephemeral Storage & Data Retention Manager for CyberGuard AI.
Compliant with DPDP Act, 2023 principles of Storage Limitation & Purpose Specification.

Automatically purges temporary uploaded screenshots, audio files, and cached media older than
the retention threshold (default: 24 hours), ensuring user data is never stored indefinitely.
"""
import time
import logging
from pathlib import Path
from typing import List, Dict, Any

from config import settings

logger = logging.getLogger(__name__)

DEFAULT_RETENTION_SECONDS = 24 * 3600  # 24 Hours


def purge_expired_artifacts(
    directories: List[Path] = None,
    max_age_seconds: int = DEFAULT_RETENTION_SECONDS
) -> Dict[str, Any]:
    """
    Deletes files older than max_age_seconds from specified directories.
    Excludes .gitkeep and permanent templates.
    """
    if directories is None:
        directories = [settings.UPLOAD_DIR, settings.AUDIO_DIR]

    now = time.time()
    purged_files = 0
    bytes_reclaimed = 0

    for dir_path in directories:
        if not dir_path.exists():
            continue
        try:
            for item in dir_path.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    file_age = now - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_size = item.stat().st_size
                        item.unlink()
                        purged_files += 1
                        bytes_reclaimed += file_size
                        logger.info(f"Purged expired temporary artifact: {item.name}")
        except Exception as e:
            logger.error(f"Error purging directory {dir_path}: {e}")

    return {
        "purged_files_count": purged_files,
        "bytes_reclaimed": bytes_reclaimed,
        "retention_window_hours": max_age_seconds / 3600,
        "status": "success"
    }

