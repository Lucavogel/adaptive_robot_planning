import json
from openai import OpenAI
from config import API_KEY, MODEL, BASE_URL
import os
import requests
from perception import get_latest_objects

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# Relations utiles pour ConceptNet
USEFUL_CN_RELATIONS = {
    "UsedFor", "Causes", "HasProperty", 
    "MotivatedBy", "IsA"
}

# Import pour emotion analyzer
try:
    from transformers import pipeline
    emotion_analyzer = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-emotion", device=-1)
    print("✅ Emotion analyzer chargé avec succès")
except ImportError:
    emotion_analyzer = None
    print("⚠️ Emotion analysis non disponible - transformers non installé")
except Exception as e:
    emotion_analyzer = None
    print(f"⚠️ Erreur chargement emotion analyzer: {e}")

def load_knowledge_graph(path=None):
    """Charger le graphe de connaissances depuis le fichier JSON"""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "knowledge_graph.json")
    try:
        with open(path, "r") as f:
            kg = json.load(f)
        return kg
    except FileNotFoundError:
        print(f"Fichier knowledge_graph.json non trouvé dans {path}")
        return {"entities": {}}
    except json.JSONDecodeError:
        print(f"Erreur de format JSON dans {path}")
        return {"entities": {}}

def format_kg(kg: dict) -> str:
    lines = []
    for subject, relation in kg.items():
        for predicate, obj in relation.items():
            lines.append(f"{subject} --{predicate}--> {obj}")
    return "\n".join(lines)

# NOUVELLES FONCTIONS AJOUTÉES
def get_entity_relations(keyword, kg_json):
    """Extraire les relations d'une entité du graphe de connaissances"""
    entities = kg_json.get("entities", {})
    entity = None
    
    # Chercher l'entité (insensible à la casse)
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
        # Fallback vers ConceptNet si l'entité n'est pas dans le graphe local
        relations_list = query_conceptnet_filtered(keyword)

    return relations_list

def query_conceptnet_filtered(keyword, lang="en", limit=50):
    """Requête ConceptNet avec filtrage des relations pertinentes"""
    url = f"http://api.conceptnet.io/c/{lang}/{keyword.lower()}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        edges = data.get("edges", [])[:limit]
        if not edges:
            return [f"[ConceptNet] Aucune info pour '{keyword}'."]
        
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
        
        return output if output else [f"[ConceptNet] Aucune info utile pour '{keyword}'."]
    except Exception as e:
        return [f"[ERREUR] Requête ConceptNet échouée: {e}"]

def get_multiple_entities_relations(keywords, kg_json):
    """Extraire les relations pour plusieurs entités"""
    result = {}
    for word in keywords:
        result[word] = get_entity_relations(word, kg_json)
    return result

def analyze_emotion(text):
    """Analyser l'émotion du texte utilisateur"""
    if not text or text.strip() == "":
        return "neutral"
    
    if emotion_analyzer is None:
        return "neutral"
    
    try:
        result = emotion_analyzer(text)
        emotion = result[0]['label'] if result else "neutral"
        return emotion.lower()
    except Exception as e:
        print(f"Erreur analyse émotion: {e}")
        return "neutral"

def reason_with_context(context_description, current_exercise, next_exercise, dialogue_history=None, user_input="", use_enhanced=True):
    """
    Fonction de raisonnement principale (version améliorée par défaut)
    """
    # Charger le graphe de connaissances
    kg = load_knowledge_graph()
    
    # Obtenir les objets détectés
    try:
        detected_objects = get_latest_objects()
    except Exception as e:
        print(f"Erreur récupération objets: {e}")
        detected_objects = []
    
    # Analyser l'émotion de l'utilisateur
    user_emotion = analyze_emotion(user_input) if user_input else "neutral"
    
    # Concepts pertinents basés sur les objets détectés et le contexte
    base_concepts = ["Coffee", "Banana", "GlassOfWater", "HotDay", "Towel"]
    concepts = base_concepts.copy()
    
    # Ajouter des concepts basés sur les objets détectés
    for obj in detected_objects:
        obj_lower = obj.lower()
        if obj_lower in ["cup", "glass"]:
            if "GlassOfWater" not in concepts:
                concepts.append("GlassOfWater")
        elif obj_lower == "banana":
            if "Banana" not in concepts:
                concepts.append("Banana")
        elif obj_lower == "towel":
            if "Towel" not in concepts:
                concepts.append("Towel")
    
    # Extraire les relations du graphe de connaissances
    concepts_relations = get_multiple_entities_relations(concepts, kg)
    
    # Préparer l'historique de dialogue
    history_str = []
    if dialogue_history:
        history_str = dialogue_history[-5:]  # Garder seulement les 5 derniers échanges
    
    # Appel au LLM avec le système amélioré
    return query_llm_about_entities(
        concepts_relations=concepts_relations,
        user_state=user_emotion,
        user_answer=user_input,
        current_exercise=current_exercise,
        next_exercise=next_exercise,
        history_str=history_str,
        context_description=context_description,
        detected_objects=detected_objects
    )

def query_llm_about_entities(concepts_relations, user_state, user_answer="", current_exercise="Stretch your arms above your head for 5 seconds", next_exercise="Touch your toes for 5 seconds", history_str=[], context_description="", detected_objects=[]):
    """
    Requête LLM avec les relations du graphe de connaissances
    """
    # Construire le texte des relations
    relations_text = "Relations dans le graphe de connaissances :\n\n"
    for concept, rels in concepts_relations.items():
        if rels:  # Vérifier que la liste n'est pas vide
            relations_text += f"[{concept}]\n"
            relations_text += "\n".join(rels) + "\n\n"
    
    # Construire l'historique formaté
    history_text = ""
    if history_str:
        history_text = "\n".join(history_str[-3:])  # Derniers 3 échanges
    
    prompt = f"""
You are StretchBot, a friendly robot that helps a human with their morning stretching routine. Your job is to support them with kind words, suggestions, and simple help.

**IMPORTANT: Command Recognition**
- If the user says "point to [object]", "point [object]", or just "[object name]", this is a ROBOT COMMAND, not a stretch exercise
- For robot commands, you should generate: POINT_[OBJECT_NAME] (using the exact object detected)
- Available objects detected: {detected_objects}
- Objects with ArUco markers available for pointing: {[obj for obj in detected_objects if 'cell phone' in obj.lower() or 'cup' in obj.lower() or 'banana' in obj.lower()]}

Context:
- Current stretch: {current_exercise}
- Next stretch: {next_exercise}
- Situation: {context_description}
- User emotional state: {user_state}
- Objects available: {detected_objects}
- Dialogue history: {history_str}
- Helpful knowledge: 
{relations_text}

The user has responded: "{user_answer}"

Instructions:
- **PRIORITY 1**: If user says "point to [object]" or similar, respond with POINT_[OBJECT] using exact detected object names
- If the user completed the current stretch and is feeling well, start your response with: NEXT_EXERCISE: and explain the next stretch briefly.
- If the user is tired, confused, or needs support, you can offer help like water, food, or a break.
- If you want to point to an object in front of you to offer it (like a glass, banana, or towel), start your response with: POINT_<OBJECT>. Then continue normally.
- If the current exercise status is "not yet", encourage the user to keep trying and give helpful advice. 
- If you are sure the user wants to skip, start your output with NEXT_EXERCISE: followed by a brief explanation of the next stretch.
- If the user wants to stop or it's better to stop the routine or it is the last exercise, start with: STOP_ROUTINE.
- Otherwise: Just speak naturally and supportively.

Object Command Mapping:
- "cell phone" detected → use POINT_CELL_PHONE
- "cup" detected → use POINT_CUP  
- "banana" detected → use POINT_BANANA
- "glass" mentioned by user → use POINT_CUP (if cup detected)

Examples:
1. If the user says "point to cell phone" and cell phone is detected:
   Reasoning: User is giving a robot command to point to the cell phone which is detected.
   Output: POINT_CELL_PHONE Sure! Let me point to your phone for you.

2. If the user says "That was hard but I did it!", and status = "success":
   Reasoning: The user completed the task. Status confirms success. It's time to proceed.
   Output: NEXT_EXERCISE: Great job! Now, let's touch our toes. Keep your knees soft and reach gently.

3. If the user says "I can't bend that far…" and gives up after two tries:
   Reasoning: User has clearly said they can't complete the stretch. It's best to move on.
   Output: NEXT_EXERCISE: That's okay! Let's lean left and right next. Just sway gently side to side.

4. If the user looks tired but hasn't refused help yet:
   Reasoning: User seems fatigued. A gentle offer of support might help.
   Output: POINT_CUP Want a sip of water before we continue? Or would you prefer the banana?

5. If the user says "stop" or "I want to stop" or "enough":
   Reasoning: User wants to stop the routine completely.
   Output: STOP_ROUTINE Okay, stopping the routine. Have a great day!
 
Answer like this:
Reasoning: <short explanation of why you say what you say>
Output: <short, friendly response (1–2 sentences)>
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert wellness coach with knowledge graph reasoning capabilities."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            extra_body={}
        )

        if response and response.choices and len(response.choices) > 0:
            return response.choices[0].message.content
        else:
            return "Désolé, je n'ai pas pu traiter votre demande."

    except Exception as e:
        print(f"⚠️ ERREUR API: {e}")
        
        # Si l'utilisateur dit "stop", forcer STOP_ROUTINE
        if user_answer and any(word in user_answer.lower() for word in ["stop", "quit", "exit", "arrêt"]):
            return "Reasoning: User requested to stop and API is down.\nOutput: STOP_ROUTINE Okay, stopping the routine due to technical issues."
        
        return "Désolé, j'ai un problème technique. Continuons avec l'exercice."

# Test du système (si exécuté directement)
if __name__ == "__main__":
    # Test simple
    print("=== Test du système de raisonnement amélioré ===")
    
    result = reason_with_context(
        context_description="L'utilisateur est dans son salon avec une tasse et un ordinateur portable",
        current_exercise="Stretch your arms",
        next_exercise="Touch your toes",
        dialogue_history=["Human: Je commence à transpirer"],
        user_input="Je commence à transpirer"
    )
    
    print("\n🧠 Réponse du système :")
    print(result)

