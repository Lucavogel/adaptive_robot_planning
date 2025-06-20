import json
from openai import OpenAI
from config import API_KEY, MODEL, BASE_URL

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

def reason_with_context(context_description, current_exercise, next_exercise, dialogue_history=None):
    kg = load_knowledge_graph()
    formatted_kg = format_kg(kg)

    history_str = ""
    if dialogue_history:
        history_str = "\nDialogue history:\n" + "\n".join(dialogue_history)

    prompt = f"""
You are StretchBot, a friendly and empathetic robot coach guiding a human through a safe and supportive morning stretching routine and normal conversations.
your stretching plan is :

Stretch your arms
Touch your toes
Rotate your neck
stretching session finished

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
8. if the user is asking a question alweys answer it with something related to that question, even if it is not related to the current exercise.

IMPORTANT:
- If it's appropriate to start the next exercise, begin your Output line with: NEXT_EXERCISE:
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

    return response.choices[0].message.content
