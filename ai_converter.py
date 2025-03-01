from transformers import pipeline

# ✅ Laadt een OpenAI of Hugging Face model voor code-generatie
code_converter = pipeline("text2text-generation", model="facebook/bart-large")

def convert_code(legacy_code: str, source_lang: str, target_lang: str) -> str:
    """
    Converteert legacy-code naar een moderne taal met AI
    """
    prompt = f"Convert {source_lang} code to {target_lang}: \n{legacy_code}"
    output = code_converter(prompt, max_length=500)
    return output[0]['generated_text']

# 🔥 Test AI-conversie
if __name__ == "__main__":
    legacy_code = "PRINT 'Hello, world!'"
    print(convert_code(legacy_code, "Basic", "Python"))
