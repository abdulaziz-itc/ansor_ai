import uuid
import os
import logging
import edge_tts
from typing import Optional

# Logger sozlash
logger = logging.getLogger("ansor_ai.audio_service")

class AudioService:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Standart ovozlar (Microsoft Edge)
        self.voices = {
            "Uzbek": "uz-UZ-MadinaNeural",
            "Russian": "ru-RU-SvetlanaNeural",
            "English": "en-US-GuyNeural"
        }
        logger.info(f"AudioService yuklandi: OutputDir={self.output_dir}")

    async def generate_audio(self, text: str, lang: str = "Uzbek") -> str:
        """
        Matndan yuqori sifatli MP3 audio fayl yaratadi.
        Microsoft Edge TTS (edge-tts) dan foydalanadi.
        """
        if not text:
            logger.warning("Audio yaratish uchun matn yo'q.")
            return ""

        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        # Tilga mos ovozni tanlash
        voice = self.voices.get(lang, self.voices["Uzbek"])
        
        logger.info(f"Audio yaratilmoqda ({lang} - {voice}): {text[:30]}...")
        
        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(filepath)
            
            # Fayl hajmini tekshirish
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                logger.info(f"Audio muvaffaqiyatli yaratildi: {filename} ({size} bytes)")
            
            return filename
            
        except Exception as e:
            logger.error(f"Audio yaratishda xatolik: {str(e)}", exc_info=True)
            raise Exception(f"TTS xatosi: {str(e)}")

# Statik audio papkasi bilan servisni ishga tushirish
audio_service = AudioService("static/audio")
