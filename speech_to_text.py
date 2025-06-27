import sounddevice as sd
import queue
import vosk
import json
import time
import os

q = queue.Queue()

# 🔧 Chemin vers le modèle Vosk
model_path = os.path.join(os.path.dirname(__file__), "vosk-model-small-en-us-0.15")
model = vosk.Model(model_path)

def _callback(indata, status):
    if status:
        print(status)
    q.put(bytes(indata))

def listen_until_silent(timeout=1.8):
    print(" Listening (stop talking for", timeout, "s to end)...")
    rec = vosk.KaldiRecognizer(model, 16000)
    silence_start = None
    full_text = ""

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=_callback):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                full_text += result.get("text", "") + " "
                silence_start = time.time()
            else:
                partial = json.loads(rec.PartialResult())["partial"]
                if partial:
                    silence_start = time.time()

            if silence_start and (time.time() - silence_start) > timeout:
                break

    return full_text.strip()
