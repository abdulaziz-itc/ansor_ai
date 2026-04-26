import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

# Load .env from the project root (backend folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path, override=True)

class AIService:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-flash-latest')

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

        # USE RAW REST API TO BYPASS SDK BUGS
        import json
        import urllib.request
        
        api_key = os.getenv("GOOGLE_API_KEY")
        # Let's try the -latest suffix just in case
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
        
        # Google API requires camelCase for JSON!
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"fileData": {"mimeType": video_file.mime_type, "fileUri": video_file.uri}}
                    ]
                }
            ]
        }
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req) as api_response:
                result = json.loads(api_response.read().decode('utf-8'))
                text_response = result['candidates'][0]['content']['parts'][0]['text']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            
            # Fetch available models to debug!
            try:
                models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                models_req = urllib.request.Request(models_url)
                with urllib.request.urlopen(models_req) as m_res:
                    models_data = json.loads(m_res.read().decode('utf-8'))
                    avail_models = [m['name'] for m in models_data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
                    error_body += f" \n\nAVAILABLE MODELS ON THIS KEY: {', '.join(avail_models)}"
            except Exception as ex:
                error_body += f" (Could not fetch models: {str(ex)})"
                
            print(f"REST API HTTP Error: {error_body}")
            raise Exception(f"Google API Error: {error_body}")
        except Exception as e:
            print(f"REST API General Error: {e}")
            raise Exception(f"Google API Failed: {str(e)}")
        
        # Clean up: delete the file from Google servers
        genai.delete_file(video_file.name)
        
        return text_response.strip()

ai_service = AIService()
