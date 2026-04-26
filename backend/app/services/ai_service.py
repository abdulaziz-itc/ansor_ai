import google.generativeai as genai
import time
import json
import urllib.request
import os

# KESHDAN QUTILISH UCHUN KALIT TO'G'RIDAN-TO'G'RI KODGA YOZILDI
API_KEY = "REMOVED_API_KEY"

class AIService:
    def __init__(self):
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def translate_video(self, video_path: str) -> str:
        print(f"Uploading file: {video_path}")
        video_file = genai.upload_file(path=video_path)
        print(f"File uploaded: {video_file.name}")

        while video_file.state.name == "PROCESSING":
            print("Processing video...")
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise Exception("Video processing failed on Google servers.")

        prompt = (
            "You are an expert in sign language translation. "
            "Please watch this video and translate the sign language into clear text. "
            "Return only the translated text, nothing else. "
            "If no sign language is detected, describe what is happening in the video briefly."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
        
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
            raise Exception(f"Google API Error: {error_body}")
        except Exception as e:
            raise Exception(f"Google API Failed: {str(e)}")
        
        genai.delete_file(video_file.name)
        return text_response.strip()

ai_service = AIService()
