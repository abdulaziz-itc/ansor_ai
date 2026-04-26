import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv(override=True)
print("GenerativeAI version:", getattr(genai, '__version__', 'unknown'))
print("API Key loaded:", bool(os.getenv("GOOGLE_API_KEY")))

try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Model initialized.")
    response = model.generate_content("Hello, this is a test. Just say OK.")
    print("API SUCCESS! Response:", response.text)
except Exception as e:
    print("\nAPI ERROR!")
    print(str(e))
