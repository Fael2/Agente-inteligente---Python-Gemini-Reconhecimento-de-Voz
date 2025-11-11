# agent_gemini_final_v2.py
import os
import sys
import time
import textwrap
from pathlib import Path
from google import genai
import speech_recognition as sr
import pyttsx3
import fitz  # PyMuPDF
import numpy as np
from gtts import gTTS
from playsound import playsound
import tempfile
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ============= CONFIGURAÇÕES =============
PDF_PATH = "manual_veiculo.pdf"
TXT_PATH = "manual.txt"
TOP_K = 3
MAX_PROMPT_CHARS = 12000
# =========================================

# Inicializa cliente Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ Defina GEMINI_API_KEY no ambiente antes de rodar.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

# Tenta escolher modelo automaticamente
def get_best_model():
    models = [m.name for m in client.models.list()]
    if "models/gemini-2.5-pro" in models:
        return "models/gemini-2.5-pro"
    elif "models/gemini-2.5-flash" in models:
        return "models/gemini-2.5-flash"
    elif "models/gemini-pro-latest" in models:
        return "models/gemini-pro-latest"
    else:
        return models[0]

MODEL_NAME = get_best_model()
print(f"🧠 Usando modelo: {MODEL_NAME}")

# Inicializa voz
def init_tts():
    try:
        engine = pyttsx3.init(driverName='sapi5')
    except Exception:
        engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 170)
    engine.setProperty('volume', 1.0)
    return engine

tts = init_tts()

def speak(text):
    """Fala a resposta usando gTTS e playsound (voz natural e estável)."""
    if not text or not text.strip():
        return
    try:
        # Limpa o texto para evitar pausas ou quebras incorretas
        clean_text = " ".join(text.split())

        # Caminho fixo (evita erro do NamedTemporaryFile no Windows)
        audio_path = os.path.join(os.getcwd(), "resposta.mp3")

        # Gera o áudio
        tts = gTTS(text=clean_text, lang="pt")
        tts.save(audio_path)

        # Reproduz
        print("🔊 Falando resposta...")
        playsound(audio_path)

        # Remove o arquivo após tocar
        os.remove(audio_path)
    except Exception as e:
        print("⚠️ Erro ao reproduzir áudio:", e)


# Carrega texto do manual
def load_manual():
    if Path(PDF_PATH).exists():
        print(f"📘 Extraindo texto do PDF: {PDF_PATH}")
        doc = fitz.open(PDF_PATH)
        return "\n".join(p.get_text("text") for p in doc)
    elif Path(TXT_PATH).exists():
        print(f"📗 Lendo texto do arquivo: {TXT_PATH}")
        return Path(TXT_PATH).read_text(encoding="utf-8", errors="ignore")
    else:
        print("❌ Nenhum manual encontrado.")
        sys.exit(1)

# Quebra texto em parágrafos
def chunk_text(text, min_chars=100):
    lines = [l.strip() for l in text.splitlines()]
    paras, buf = [], ""
    for line in lines:
        if not line:
            if buf:
                paras.append(buf.strip())
                buf = ""
        else:
            if len(line) < 80:
                buf += " " + line
            else:
                if buf:
                    paras.append(buf.strip())
                buf = line
    if buf:
        paras.append(buf.strip())
    merged = []
    for p in paras:
        if len(p) < min_chars and merged:
            merged[-1] += " " + p
        else:
            merged.append(p)
    return merged

# Monta índice local (TF-IDF)
def build_index(paras):
    vec = TfidfVectorizer(stop_words="english")
    mat = vec.fit_transform(paras)
    return vec, mat

def search_manual(query, vec, mat, paras, k=TOP_K):
    qv = vec.transform([query])
    sims = cosine_similarity(qv, mat).flatten()
    idxs = sims.argsort()[-k:][::-1]
    return [(i, sims[i], paras[i]) for i in idxs]

# Chama Gemini
def call_gemini(prompt):
    try:
        resp = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        if hasattr(resp, "text"):
            return resp.text.strip()
        if hasattr(resp, "candidates") and resp.candidates:
            return resp.candidates[0].content.parts[0].text
        return None
    except Exception as e:
        print("❌ Erro ao chamar Gemini:", e)
        return None

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Ajustando ruído ambiente...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("🔔 Fale após o beep...")
        import winsound
        winsound.Beep(800, 200)
        audio = r.listen(source, timeout=6, phrase_time_limit=10)
    try:
        txt = r.recognize_google(audio, language="pt-BR")
        print(f"🗣️ Você disse: {txt}")
        return txt
    except Exception:
        return ""

def build_prompt(question, results):
    ctx = "\n\n".join([f"[Trecho {i+1} | score={score:.3f}]\n{chunk}" for i, (idx, score, chunk) in enumerate(results)])
    prompt = f"""
Você é um assistente técnico automotivo.
Baseie-se apenas nas informações abaixo do manual para responder à pergunta de forma direta e clara.

Contexto:
{ctx}

Pergunta: {question}
Resposta:
"""
    return prompt[:MAX_PROMPT_CHARS]

# Main
def main():
    text = load_manual()
    paras = chunk_text(text)
    print(f"✅ {len(paras)} parágrafos preparados.")
    vec, mat = build_index(paras)

    speak("Agente com Gemini iniciado. Diga 'finalizar' para encerrar.")
    print("\n🤖 AGENTE ATIVO — pressione Enter para falar, ou digite sua pergunta.\n")

    while True:
        query = input("👉 ").strip()
        if not query:
            query = listen()
        if not query:
            continue
        if query.lower() in ("finalizar", "sair", "encerrar"):
            speak("Encerrando. Até mais!")
            sys.exit(0)

        print("🔎 Buscando informações relevantes...")
        results = search_manual(query, vec, mat, paras, k=TOP_K)
        prompt = build_prompt(query, results)
        print(f"📨 Enviando contexto ao modelo {MODEL_NAME}...")

        answer = call_gemini(prompt)
        if not answer:
            speak("Não consegui resposta do Gemini. Lendo o trecho do manual.")
            combined = " ".join([chunk for _, _, chunk in results])
            print("\n--- TRECHOS ---\n", combined)
            speak(combined)
        else:
            print("\n--- RESPOSTA ---\n", answer)
            speak(answer)

if __name__ == "__main__":
    main()
