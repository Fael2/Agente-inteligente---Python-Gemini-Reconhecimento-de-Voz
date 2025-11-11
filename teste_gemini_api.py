from google import genai
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
model = "gemini-1.5-flash"

try:
    response = client.models.generate_content(
        model=model,
        contents="Explique resumidamente como trocar um pneu de carro."
    )
    print("✅ Conectou com sucesso!")
    print(response.text)
except Exception as e:
    print("❌ Erro ao acessar Gemini:")
    print(e)
