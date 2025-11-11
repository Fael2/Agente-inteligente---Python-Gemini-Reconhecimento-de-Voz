from gtts import gTTS
from playsound import playsound
import os

# Texto de teste
texto = "Olá, este é um teste da voz natural do agente Gemini!"

# Caminho seguro para salvar o áudio
audio_path = os.path.join(os.getcwd(), "voz_teste.mp3")

try:
    # Cria e salva o áudio
    tts = gTTS(text=texto, lang="pt")
    tts.save(audio_path)
    print("✅ Áudio gerado com sucesso!")

    # Reproduz o áudio
    playsound(audio_path)
    print("🔊 Fala reproduzida com sucesso!")

    # (Opcional) apaga o arquivo depois de tocar
    os.remove(audio_path)

except Exception as e:
    print("⚠️ Erro:", e)
