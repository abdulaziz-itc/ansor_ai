import os
import time
import logging
from typing import List

logger = logging.getLogger("ansor_ai.file_service")

class FileService:
    def __init__(self, dirs: List[str]):
        self.dirs = dirs
        for d in self.dirs:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)

    def cleanup_old_files(self, max_age_seconds: int = 3600 * 24):
        """Eski vaqtinchalik fayllarni o'chirish."""
        now = time.time()
        count = 0
        for directory in self.dirs:
            if not os.path.exists(directory): continue
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    if (now - os.path.getmtime(filepath)) > max_age_seconds:
                        try:
                            os.remove(filepath)
                            count += 1
                        except: pass
        if count > 0: logger.info(f"Cleanup: {count} ta fayl tozalandi.")

# Barcha media papkalarini qo'shamiz
file_service = FileService(["uploads", "static/audio", "uploads/files", "uploads/stickers"])
