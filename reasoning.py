import json
from openai import OpenAI
from config import API_KEY
import requests
from perception import get_environment_context_test
MODEL = "deepseek/deepseek-r1-0528-qwen3-8b:free"
BASE_URL = "https://openrouter.ai/api/v1"
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

def load_knowledge_graph(path="knowledge_graph.json"):
    with open(path, "r") as f:
        kg = json.load(f)
    return kg

def format_kg(kg: dict) -> str:
    lines = []
    for subject, relation in kg.items():
        for predicate, obj in relation.items():
            lines.append(f"{subject} --{predicate}--> {obj}")
    return "\n".join(lines)

'''def reason_with_context(context_description, current_exercise, next_exercise, dialogue_history="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"):
    kg = load_knowledge_graph()
    formatted_kg = format_kg(kg)

    history_str = ""
    if dialogue_history:
        history_str = "\nDialogue history:\n" + "\n".join(dialogue_history)

    prompt = f"""
You are StretchBot, a friendly and empathetic robot coach guiding a human through a safe and supportive morning stretching routine and normal conversations.
Your stretching plan is:

Stretch your arms above your head for 5 seconds
Touch your toes for 5 seconds
lean left and right for 5 seconds each

Current exercise: {current_exercise}
Next exercise: {next_exercise}

Context:
{context_description}
{history_str}

Relevant commonsense knowledge:
{formatted_kg}

Your instructions:
1. Analyze the user's current state based on the context and recent dialogue.
2. If the user feels fine, gently propose moving on to the next exercise: {next_exercise}, with clear instructions.
3. If the user seems tired, tense, or has previously expressed discomfort, suggest help (e.g., break, water, encouragement), but do NOT repeat offers they already refused.
4. Always prioritize the user's most recent response.
5. Do not offer the same help more than once unless the user expresses a new need.
6. Speak with short, warm, and simple sentences. Use friendly language. Congratulate or encourage when appropriate.
7. Ask a caring question if you think the user may be struggling or needs support.
8. If the user is asking a question, always answer it with something related to that question, even if it is not related to the current exercise.
9. If you want the robot to point to an object detected in front of it (for example, a glass, a banana, or a towel), start your Output line with: POINT_<OBJECT> (for example: POINT_GLASS, POINT_BANANA, POINT_TOWEL), then continue your sentence naturally.
10. If the user wants to stop the stretching routine, or if you think it is necessary to stop for safety or well-being, or if the routine is over, start your Output line with: STOP_ROUTINE — this will be your final message to the user.

- You will receive a line like 'Exercise status: success' or 'Exercise status: not yet' in the context.
- If the status is 'success', congratulate the user and propose to move to the next exercise and only go to the next exercice if he succeded.
- If the status is 'not yet', encourage the user to keep trying and give advice.

IMPORTANT:
- If it's appropriate to start the next exercise, begin your Output line with: NEXT_EXERCISE:
- If you want the robot to point to an object, begin your Output line with: POINT_<OBJECT> (replace <OBJECT> by the object name in English and uppercase, e.g., POINT_GLASS).
- If the user wants to stop or you decide to stop the stretching routine because you have no more exercices left, begin your Output line with: STOP_ROUTINE , it will be your final message to the user.
- Otherwise, respond naturally and empathetically to the user.

Format your reply like this and only one time:

Reasoning:
<step-by-step reasoning>

Output: <what the robot should say or ask next in 1–2 sentences>

"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        extra_body={}
    )

    # Ajout de la vérification de None et du contenu attendu
    if (
        response is None or
        not hasattr(response, "choices") or
        not response.choices or
        not hasattr(response.choices[0], "message") or
        not hasattr(response.choices[0].message, "content")
    ):
        return "Sorry, I can't answer right now (API error or rate limit)."

    return response.choices[0].message.content'''

# Appel au LLM avec prompt basé sur les relations
def query_llm_about_entities(concepts_relations,user_state, user_answer = "",current_exercise="Stretch your arms above your head for 5 seconds"
                        , next_exercise="Touch your toes for 5 seconds", history_str=[], context_description="",
                        detected_objects=[]):
    print(history_str)
    relations_text = "Voici les relations dans le graphe de connaissances :\n\n"
    for concept, rels in concepts_relations.items():
        relations_text += f"[{concept}]\n"
        relations_text += "\n".join(rels) + "\n\n"

    prompt = f"""
You are StretchBot, a friendly robot that helps a human with their morning stretching routine. Your job is to support them with kind words, suggestions, and simple help.

**SITUATION TO ANALYZE:**
- Current exercise: {current_exercise}
- Next planned exercise: {next_exercise}
- Context: {context_description}
- User's physical/emotional state: {user_state}
- What the user just said: "{user_answer}"
- Available objects that might help: {detected_objects}
- Previous conversation: {history_str}
- Relevant knowledge: {concepts_relations}

**REASONING PROCESS:**
First, deeply analyze the situation by asking yourself:
- What is the user's TRUE emotional and physical state?
- What are they NOT saying that I should pick up on?
- What would a good human trainer do in this exact situation?
- What are the potential consequences of each action I could take?
- How can I best support their long-term wellness and motivation?

**INSTRUCTIONS:**
- If the user completed the current stretch,and is feeling well start your response with: NEXT_EXERCISE and explain the next stretch briefly.
- If the current exercise status is "not yet", encourage the user to keep trying and give helpful advice; but if the user wants to skip or is not able to do this exercise, start your output with NEXT_EXERCISE followed by a brief explanation of the next stretch.
- If the user is tired, confused, or needs support, you can offer help like water, food, or a break.
- If you want to point to an object in front of you to offer it (like a glass, banana, or coffee), start your response with: POINT_<OBJECT>. Then continue normally.
- If the user wants to stop or it’s better to stop the routine or it is the last exercice, start with: STOP_ROUTINE.
- Dont repeat the same offer more than once unless the user asks for it again.
- Otherwise, feel free to encourage, advise, or chat as you see fit.

**EXAMPLE OF GOOD REASONING:**
1. If the user says "That was hard but I did it!", and status = "success":
   Reasoning:
   The user completed the task. Status confirms success. It's time to proceed.
   Output: NEXT_EXERCISE Great job! Now, let's touch our toes. Keep your knees soft and reach gently.

2. If the user says "I can't bend that far…" and gives up after two tries:
   Reasoning:
   User has clearly said they can't complete the stretch. It's best to move on.
   Output: NEXT_EXERCISE That's okay! Let's lean left and right next. Just sway gently side to side.

3. If the user looks tired but hasn't refused help yet:
   Reasoning:
   User seems fatigued. A gentle offer of support might help.
   Output: POINT_GLASS Want a sip of water before we continue? Or would you prefer the banana?


**RESPONSE FORMAT:**
Reasoning: [3-4 sentences of deep analysis about what's really happening and why you're choosing this action. Show your understanding of human nature, physical limits, and emotional needs.]

Output: [Your natural, empathetic response - be genuine, not robotic]
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un expert en bien-être et raisonnement basé sur graphe de connaissances."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            extra_body={}
        )

        return response.choices[0].message.content

    except Exception as e:
        print("⚠️ ERREUR:", e)
        return "[ERROR] API call failed."
# Entrée principale