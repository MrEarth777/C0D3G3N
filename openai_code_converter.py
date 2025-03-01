import openai
import os
from dotenv import load_dotenv

# ✅ Laad API-sleutel veilig in uit .env bestand
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("🚨 API-sleutel niet gevonden. Zorg dat je .env correct is ingesteld!")

def convert_code(legacy_code, source_lang="COBOL", target_lang="Python"):
    """
    Converteert legacy-code naar een moderne programmeertaal met OpenAI Codex (GPT-4 Turbo).
    """
    prompt = f"""
Convert the following {source_lang} code to {target_lang}:
Make sure to preserve all logic and structure.
Return only the converted code without explanations.

{legacy_code}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "You are a code conversion assistant."},
                      {"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"].strip()
    
    except Exception as e:
        print(f"❌ Fout bij conversie: {str(e)}")
        return "⚠️ Conversie mislukt!"

# ✅ Test API-connectie
try:
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": "Say Hello!"}]
    )
    print("✅ API werkt! Reactie:", response["choices"][0]["message"]["content"])
except Exception as e:
    print("❌ Fout bij API-aanroep:", str(e))

# ✅ Test de AI met een voorbeeld
if __name__ == "__main__":
    legacy_code_sample = "DISPLAY 'Hello, World!'"
    converted_code = convert_code(legacy_code_sample)
    
    print("🔹 Legacy Code:")
    print(legacy_code_sample)
    print("\n✅ Geconverteerde Code:")
    print(converted_code)
legacy_code_samples = [
    {"code": "MOVE 5 TO X.", "source": "COBOL", "target": "Python"},
    {"code": "IF X > 10 THEN DISPLAY 'X is greater than 10'.", "source": "COBOL", "target": "Python"},
    {"code": "PERFORM UNTIL X = 10\n    DISPLAY 'Looping'.\nEND-PERFORM.", "source": "COBOL", "target": "Python"}
]

for sample in legacy_code_samples:
    converted_code = convert_code(sample["code"], sample["source"], sample["target"])
    print(f"\n🔹 {sample['source']} Code:\n{sample['code']}\n✅ Geconverteerde {sample['target']} Code:\n{converted_code}")
