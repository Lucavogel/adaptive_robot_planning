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

def reason_with_context(context_description):
    kg = load_knowledge_graph()
    formatted_kg = format_kg(kg)

    prompt = f"""
The robot is guiding a human through a set of morning stretches.

Context:
{context_description}

Relevant commonsense knowledge:
{formatted_kg}

Task:
1. Reason step by step what the robot should do next, using the context and knowledge graph above.
2. Consider verbal input and visual context.
3. At the end, provide a clear, single-line output of what the robot should say.

Format your response like:

Reasoning:
<your reasoning here>

Output: <the robot's next action>
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        extra_body={}
    )

    return response.choices[0].message.content
