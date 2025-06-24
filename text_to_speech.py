from gtts import gTTS
import tempfile
import os
import pygame

def speak(text, lang="en"):
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