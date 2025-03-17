import numpy as np
import time
import pyaudio
import wave
from flask import Flask, jsonify, render_template, request
import speech_recognition as sr

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Corrige acentuação no JSON

UPLOAD_FOLDER = "uploads/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Parâmetros de áudio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 256
SILENCE_THRESHOLD = 350  # Ajustável conforme necessário
SILENCE_TIME = 2.3  # Segundos de silêncio antes de parar

import requests

def traduzir_texto_mymemory(texto, idioma_origem, idioma_destino):
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": texto,
            "langpair": f"{idioma_origem}|{idioma_destino}"
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            traducao = response.json().get("responseData", {}).get("translatedText", "")
            return traducao
        else:
            return "Erro na tradução"
    except Exception as e:
        return f"Erro: {str(e)}"



def gravar_audio():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []
    silent_chunks = 0
    print("🎙 Gravando... Fale algo!")

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        volume = np.abs(np.frombuffer(data, dtype=np.int16)).mean()

        if volume < SILENCE_THRESHOLD:
            silent_chunks += 1
        else:
            silent_chunks = 0  # Reset se o som voltar

        if silent_chunks >= (SILENCE_TIME * RATE / CHUNK):
            print("🛑 Silêncio detectado! Parando gravação.")
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    audio_path = UPLOAD_FOLDER + "gravacao.wav"
    wf = wave.open(audio_path, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return audio_path


def transcrever_e_traduzir(audio_path, idioma_transcricao, idioma_traducao):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)

    try:
        # Transcrição
        text = recognizer.recognize_google(audio_data, language=idioma_transcricao)

        # Tradução com MyMemory
        idioma_origem = idioma_transcricao.split('-')[0]  # Pega "pt" de "pt-BR"
        translated_text = traduzir_texto_mymemory(text, idioma_origem, idioma_traducao)

        return text, translated_text
    except sr.UnknownValueError:
        return "🎙 Gravando... Fale algo!", ""
    except sr.RequestError:
        return "Erro ao conectar ao serviço de reconhecimento de voz.", ""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start-recording", methods=["POST"])
def start_recording():
    idioma_transcricao = request.args.get("idioma_transcricao", "pt-BR")
    idioma_traducao = request.args.get("idioma_traducao", "en")

    audio_path = gravar_audio()
    texto, traducao = transcrever_e_traduzir(audio_path, idioma_transcricao, idioma_traducao)
    return jsonify({"transcricao": texto, "traducao": traducao})


if __name__ == "__main__":
    app.run(debug=True)
