from openai import OpenAI

# Create OpenAI-compatible client for OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

# Scenario: the human stretches and says "It's hot"; robot sees a glass of water
prompt = ("""
    The robot is guiding a human through a set of morning stretches.

Context:
- The human stretches their arms upward.
- While stretching, the human says: "It's a very hot day."
- There is a glass of water on the table nearby.

Task:
1. Reason step by step what the robot should do next, using commonsense and situational awareness.
2. The reasoning should consider both verbal (what the human said) and visual context (glass of water).
3. At the end, provide a clear, single-line **output** that states what the robot is going to say.

Format your response like:

Reasoning:
<your reasoning here>

Output: <the robot's next action>
"""
)

# Send message to LLaMA 3.3 via OpenRouter
response = client.chat.completions.create(
    model="meta-llama/llama-3.3-8b-instruct:free",
    messages=[
        {"role": "user", "content": prompt}
    ]
)

# Print LLM response
print("🤖 Robot's suggestion:", response.choices[0].message.content)
