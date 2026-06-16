import sounddevice as sd
import queue
import vosk
import json
import time
import os
import sys

from config import VOSK_MODEL_PATH

q = queue.Queue()

_model = None

def get_vosk_model():
    global _model
    if _model is None:
        if not os.path.exists(VOSK_MODEL_PATH):
            print(f"Error: Vosk model not found at {VOSK_MODEL_PATH}.", file=sys.stderr)
            print("Please download it (e.g. from https://alphacephei.com/vosk/models) and extract it to the correct path.", file=sys.stderr)
            sys.exit(1)
        try:
            _model = vosk.Model(VOSK_MODEL_PATH)
        except Exception as e:
            print(f"Error loading Vosk model: {e}", file=sys.stderr)
            sys.exit(1)
    return _model

def _callback(indata, frames, time_info, status):
    if status:
        print(status)
    q.put(bytes(indata))

def listen_until_silent(timeout=1.2):
    print("🎤 Listening (stop talking for", timeout, "s to end)...")
    m = get_vosk_model()
    rec = vosk.KaldiRecognizer(m, 16000)
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
