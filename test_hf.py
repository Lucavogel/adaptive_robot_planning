import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACEHUB_API_TOKEN")

if not hf_token:
    print("HF Token missing in .env")
    exit(1)

print("Testing Hugging Face connection...")
try:
    # On utilise provider="together" ou on laisse l'API serverless par défaut qui marche souvent mieux
    hf_client = InferenceClient(api_key=hf_token)
    response = hf_client.chat.completions.create(
        model="Qwen/Qwen2.5-72B-Instruct", # Un modèle qui est souvent dispo en free via l'API serverless
        messages=[{"role": "user", "content": "Reply with only the word OK."}],
        max_tokens=10
    )
    print("Success! HF Response:", response.choices[0].message.content)
except Exception as e:
    print("Error calling Hugging Face:", str(e))
