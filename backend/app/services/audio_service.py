import uuid
import os
import asyncio
from gtts import gTTS

class AudioService:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def generate_audio(self, text: str) -> str:
        """
        Generates an MP3 file from text using gTTS as a fallback.
        Returns the filename.
        """
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        # 'tr' (Turkish) is used as a fallback since 'uz' is not supported by gTTS.
        # Turkish and Uzbek share similar alphabet and phonetics.
        tts = gTTS(text=text, lang='tr')
        
        # Save asynchronously
        await asyncio.to_thread(tts.save, filepath)
        
        return filename

# Initialize with the static audio directory
audio_service = AudioService("static/audio")
