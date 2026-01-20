import sys
import google.generativeai as genai
sys.stdout.reconfigure(encoding='utf-8')

USER_KEY = "AIzaSyDK1v5jAkvTmIqiJHG5nsgKLTfh78i-CYQ"
genai.configure(api_key=USER_KEY)

print("Listing models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
