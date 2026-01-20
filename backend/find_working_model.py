import google.generativeai as genai
import sys
import os

# Force correct encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

USER_KEY = "AIzaSyDK1v5jAkvTmIqiJHG5nsgKLTfh78i-CYQ"
genai.configure(api_key=USER_KEY)

print("--- Searching for available models ---")
try:
    found = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"FOUND VALID MODEL: {m.name}")
            found = True
            # Prefer flash or pro
            if 'flash' in m.name or 'pro' in m.name:
                print(f"RECOMMENDED: {m.name}")
                
    if not found:
        print("NO MODELS FOUND. Key might be invalid or project has no API enabled.")
except Exception as e:
    print(f"CRASH: {e}")
