import google.generativeai as genai
from src import config
from src.key_manager import key_manager

genai.configure(api_key=key_manager.get_current_key())

print("Listing available models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
