import os
import requests
from dotenv import load_dotenv

# Load your .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: Could not find API key in environment variables.")
    exit()

# Ask Google's REST API for the list of models
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)
data = response.json()

print("🌟 Available Gemini Models 🌟")
print("-" * 30)

for model in data.get('models', []):
    # We only care about models that can generate content (not just embeddings)
    if 'generateContent' in model.get('supportedGenerationMethods', []):
        # Clean up the name (removes the 'models/' prefix)
        clean_name = model['name'].replace('models/', '')
        print(f"✅ {clean_name}")