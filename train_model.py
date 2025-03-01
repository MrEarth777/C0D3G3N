import openai
import os
from dotenv import load_dotenv

# ✅ Laad API-key uit een .env bestand
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("❌ OpenAI API key niet gevonden! Zorg voor een .env bestand.")

# ✅ Start training (voorbeeld)
def train_model():
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="Schrijf een Python functie die twee getallen optelt.",
        max_tokens=100
    )
    print(response.choices[0].text)

train_model()
