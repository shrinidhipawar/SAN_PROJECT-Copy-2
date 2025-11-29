import google.generativeai as genai
import os

def load_api_key():
    if os.path.exists("gemini_key.txt"):
        with open("gemini_key.txt", "r") as f:
            return f.read().strip()
    return None

api_key = load_api_key()
if api_key:
    genai.configure(api_key=api_key)
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("No API key found.")
