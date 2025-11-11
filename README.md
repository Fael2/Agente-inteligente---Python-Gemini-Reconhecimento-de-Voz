# 🤖 Agente Inteligente com Gemini e Voz (Python)

Este projeto implementa um **assistente inteligente** que:

- Lê e processa um manual em **PDF**
- Aceita **comandos de voz**
- Faz **pesquisa inteligente** no manual
- Responde com **voz sintetizada natural**

---

## Tecnologias utilizadas
- Python 3.11+
- Google Gemini API
- gTTS (voz natural)
- SpeechRecognition
- TF-IDF + Scikit-learn
- PyMuPDF (leitura de PDF)

---

## 🚀 Como executar

1. Crie um ambiente virtual:
    ```bash
    python -m venv .venv
    .venv\Scripts\activate

2. Instale as dependências:
    pip install -r requirements.txt

3. Configure sua chave da API Gemini::
    setx GEMINI_API_KEY "sua_chave_aqui"

4. Execute o agente:
    python agent_gemini_final_v2.py

