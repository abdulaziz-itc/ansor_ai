import os
import time
import logging
from typing import List

# Logger sozlash
logger = logging.getLogger("ansor_ai.file_service")

class FileService:
    def __init__(self, dirs: List[str]):
        self.dirs = dirs
        for d in self.dirs:
            if not os.path.exists(d):
                os.makedirs(d)

    def cleanup_old_files(self, max_age_seconds: int = 3600 * 24):
        """
        Berilgan papkalardagi eski (masalan, 24 soatdan oshgan) fayllarni o'chiradi.
        """
        now = time.time()
        count = 0
        
        for directory in self.dirs:
            if not os.path.exists(directory):
                continue
                
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                
                # Fayl yaratilgan vaqtini tekshirish
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    
                    if file_age > max_age_seconds:
                        try:
                            os.remove(filepath)
                            count += 1
                            logger.info(f"Eski fayl o'chirildi: {filepath}")
                        except Exception as e:
                            logger.error(f"Faylni o'chirishda xato ({filepath}): {str(e)}")
                            
        if count > 0:
            logger.info(f"Cleanup yakunlandi: {count} ta fayl tozalandi.")
        else:
            logger.debug("Tozalash uchun eski fayllar topilmadi.")

# Yuklash va audio papkalari bilan servisni ishga tushirish
file_service = FileService(["uploads", "static/audio"])
