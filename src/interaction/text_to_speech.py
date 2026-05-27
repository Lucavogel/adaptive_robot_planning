from gtts import gTTS
import tempfile
import os
import pygame

def speak(text, lang="en"):
    if not text or not text.strip():
        # Do nothing if text is empty or only whitespace
        return
    # Create temp file and close it before playback
    fp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    try:
        tts = gTTS(text=text, lang=lang)
        tts.save(fp.name)
        fp.close()  # Close so pygame can access it

        pygame.mixer.init()
        pygame.mixer.music.load(fp.name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        pygame.mixer.quit()
    finally:
        os.remove(fp.name)

from gradio_client import Client
from playsound import playsound

def speak_text_realistic(
    prompt: str,
    voice: str = "alloy",
    emotion: str = "neutral",
    use_random_seed: bool = True,
    specific_seed: int = 12345
):
    client = Client("NihalGazi/Text-To-Speech-Unlimited")
    audio_path, status = client.predict(
        prompt=prompt,
        voice=voice,
        emotion=emotion,
        use_random_seed=use_random_seed,
        specific_seed=specific_seed,
        api_name="/text_to_speech_app"
    )
    print("", status)
    print(" Lecture en cours :", audio_path)
    playsound(audio_path)

if __name__ == "__main__":
    # Exemple d'utilisation
    speak("Hello, how are you today?")
    speak_text_realistic("Hello, how are you today?", voice="alloy", emotion="happy")

