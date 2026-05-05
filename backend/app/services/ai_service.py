import logging
import os
import time
import asyncio
import google.generativeai as genai
from dotenv import load_dotenv

# Logger sozlash
logger = logging.getLogger("ansor_ai.ai_service")

# .env yuklash
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path, override=True)

class AIService:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.error("GOOGLE_API_KEY topilmadi!")
        
        genai.configure(api_key=self.api_key)
        # Barqarorlik uchun 'gemini-1.5-flash' modelidan foydalanamiz
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.model = genai.GenerativeModel(self.model_name)
        logger.info(f"AIService yuklandi: Model={self.model_name}")

    async def translate_video(self, video_path: str, target_lang: str = "Uzbek") -> str:
        """
        Videoni tahlil qiladi va imo-ishora tilini berilgan tilga tarjima qiladi.
        """
        logger.info(f"Videoni Google serveriga yuklash: {video_path}")
        
        try:
            # 1. Videoni yuklash
            video_file = genai.upload_file(path=video_path)
            logger.info(f"Video yuklandi: {video_file.name}")

            # 2. Ishlov berish jarayonini kutish
            attempts = 0
            while video_file.state.name == "PROCESSING":
                if attempts > 30: # 60 soniya kutish
                    raise Exception("Video processing timeout on Google servers.")
                logger.debug("Google video tahlilini kutyapti...")
                await asyncio.sleep(2)
                video_file = genai.get_file(video_file.name)
                attempts += 1

            if video_file.state.name == "FAILED":
                raise Exception(f"Video processing failed: {video_file.state.name}")

            # 3. Mukammallashtirilgan prompt
            prompt = (
                f"Siz imo-ishora tilini tarjima qilish bo'yicha mutaxassis emassiz. "
                f"Iltimos, ushbu videoni tomosha qiling va undagi imo-ishoralarni aniq {target_lang} tiliga tarjima qiling. "
                f"Faqat tarjima matnini qaytaring, ortiqcha izohlar kerak emas. "
                f"Agar imo-ishora aniqlanmasa, videoda nima sodir bo'layotganini qisqacha {target_lang} tilida tasvirlang."
            )

            # 4. Content generation (Retry logic bilan)
            logger.info("AI tarjimani boshlamoqda...")
            response = await asyncio.to_thread(
                self.model.generate_content, [prompt, video_file]
            )
            
            result_text = response.text.strip()
            logger.info("AI tarjimasi muvaffaqiyatli yakunlandi.")
            
            # 5. Faylni Google serveridan o'chirish (joy tejash uchun)
            genai.delete_file(video_file.name)
            
            return result_text

        except Exception as e:
            logger.error(f"AIService tarjima xatosi: {str(e)}", exc_info=True)
            raise Exception(f"AI tahlilida xatolik: {str(e)}")

ai_service = AIService()
