import os
from dotenv import load_dotenv

# Charge automatiquement les variables depuis le fichier .env
load_dotenv()

BASE_URL="https://openrouter.ai/api/v1"
API_KEY=os.getenv("OPENROUTER_API_KEY", "")
MODEL="nex-agi/nex-n2-pro:free" # Or another active free model from OpenRouter

VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "data/models/vosk-model-small-en-us-0.15")
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt") # YOLO downloads automatically if just a name, or takes a path

#deepseek/deepseek-r1-0528-qwen3-8b:free
#nvidia/llama-3.3-nemotron-super-49b-v1:free

Environment = "HotDay"