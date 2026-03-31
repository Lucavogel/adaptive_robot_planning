import json
from openai import OpenAI
from config import API_KEY   # tu dois définir ça dans config.py
import requests
from perception import get_environment_context_test
from transformers import pipeline
from reasoning import query_llm_about_entities
context_description = get_environment_context_test()
MODEL = "deepseek/deepseek-r1-0528-qwen3-8b:free"
BASE_URL = "https://openrouter.ai/api/v1"

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


USEFUL_CN_RELATIONS = {
    "UsedFor", "Causes", "HasProperty",
    "MotivatedBy", "IsA"
}


def load_knowledge_graph(path="knowledge_graph.json"):
    with open(path, "r") as f:
        return json.load(f)


def get_entity_relations(keyword, kg_json):
    entities = kg_json.get("entities", {})
    entity = None
    for k, v in entities.items():
        if k.lower() == keyword.lower():
            entity = v
            keyword = k
            break

    relations_list = []
    if entity:
        relations = entity.get("relations", {})
        for rel, val in relations.items():
            if isinstance(val, list):
                for v in val:
                    relations_list.append(f"- {rel} → {v}")
            else:
                relations_list.append(f"- {rel} → {val}")
    else:
        relations_list = query_conceptnet_filtered(keyword)

    return relations_list

# Fallback ConceptNet 
def query_conceptnet_filtered(keyword, lang="en", limit=50):
    url = f"http://api.conceptnet.io/c/{lang}/{keyword.lower()}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        edges = data.get("edges", [])[:limit]
        if not edges:
            return [f"[ConceptNet] No info for '{keyword}'."]
        
        output = []
        seen = set()
        for edge in edges:
            rel = edge["rel"]["label"]
            if rel not in USEFUL_CN_RELATIONS:
                continue
            start = edge["start"]["label"]
            end = edge["end"]["label"]
            key = (rel, start, end)
            if key in seen:
                continue
            seen.add(key)
            if start.lower() == keyword.lower():
                output.append(f"- {rel} → {end}")
        return output if output else [f"[ConceptNet] No useful info for '{keyword}'."]
    except Exception as e:
        return [f"[ERROR] ConceptNet query failed: {e}"]


def get_multiple_entities_relations(keywords, kg_json):
    result = {}
    for word in keywords:
        result[word] = get_entity_relations(word, kg_json)
    return result


if __name__ == "__main__":
    kg = load_knowledge_graph()
    concepts = ["Coffee", "Banana", "GlassOfWater","HotDay","Towel",]
    question = "im starting to sweat"
    classifier = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
    emotion = classifier(question)
    label = emotion[0]['label']  
    stars = int(label[0])      
    if stars <= 2:
        emotion = "negative"
    elif stars == 3:
        emotion = "neutral"
    else:
        emotion = "positive"
    print(f"Emotion detected: {emotion}")

    print(f"emotion of text: f{classifier(question)}")
    concepts_relations = get_multiple_entities_relations(concepts, kg)
    print("✅ Relations extraites :")
    for k, v in concepts_relations.items():
        print(f"{k} → {len(v)} relations")

    result = query_llm_about_entities(concepts_relations, question)
    print("\n🧠 Réponse du LLM :")
    print(result)
