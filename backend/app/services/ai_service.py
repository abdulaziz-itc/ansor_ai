import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

# Load .env from the project root (backend folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

class AIService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def translate_video(self, video_path: str) -> str:
        """
        Uploads video to Gemini and gets the sign language translation.
        """
        print(f"Uploading file: {video_path}")
        video_file = genai.upload_file(path=video_path)
        print(f"File uploaded: {video_file.name}")

        # Wait for the file to be processed by Google
        while video_file.state.name == "PROCESSING":
            print("Processing video...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise Exception("Video processing failed on Google servers.")

        # Prompt for sign language translation
        prompt = (
            "You are an expert in sign language translation. "
            "Please watch this video and translate the sign language into clear text. "
            "Return only the translated text, nothing else. "
            "If no sign language is detected, describe what is happening in the video briefly."
        )

        response = self.model.generate_content([prompt, video_file])
        
        # Clean up: delete the file from Google servers
        genai.delete_file(video_file.name)
        
        return response.text.strip()

ai_service = AIService()
