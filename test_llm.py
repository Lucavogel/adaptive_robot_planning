import os
import urllib.request
import urllib.error
import json
from dotenv import load_dotenv

load_dotenv()

from src.config import BASE_URL

api_key = os.getenv("OPENROUTER_API_KEY")

req = urllib.request.Request(
    f"{BASE_URL}/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    data=json.dumps({
        "model": "nex-agi/nex-n2-pro:free",
        "messages": [{"role": "user", "content": "Hello! Reply with OK"}]
    }).encode('utf-8')
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("Success! Response from LLM:", result['choices'][0]['message']['content'])
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    print("Response body:", e.read().decode('utf-8'))
