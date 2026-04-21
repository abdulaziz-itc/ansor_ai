import edge_tts
import uuid
import os

class AudioService:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def generate_audio(self, text: str) -> str:
        """
        Generates an MP3 file from text using Edge-TTS.
        Returns the filename.
        """
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        # Using a high-quality Uzbek voice
        voice = "uz-UZ-MadinaNeural" 
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)
        
        return filename

# Initialize with the static audio directory
audio_service = AudioService("static/audio")
