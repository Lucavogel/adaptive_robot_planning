import os
from huggingface_hub import InferenceClient
#export HF_TOKEN="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"
# Récupération du token Hugging Face depuis les variables d'environnement
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("Set your HF_TOKEN environment variable with your Hugging Face API key.")

# Création du client Inference HF
hf_client = InferenceClient(
    provider="nscale",  # adapte selon ton provider (ou supprime si pas besoin)
    api_key=HF_TOKEN
)

def verify_with_hf_llm(llm1_output: str, context_description: str, current_exercise: str, next_exercise: str, dialogue_history: list, concepts_relations: dict = None) -> str:
    """
    Vérifie la sortie du LLM principal avec un second LLM plus neutre.
    """

    history_str = "\n".join(dialogue_history)
    
    # Format the knowledge graph relations if provided
    kg_context = ""
    if concepts_relations:
        kg_context = "\n**Available Knowledge Graph Relations:**\n"
        for concept, rels in concepts_relations.items():
            kg_context += f"[{concept}]\n"
            kg_context += "\n".join(rels) + "\n\n"

    verifier_prompt = f"""
You are a quality control assistant for StretchBot, a stretching coach robot. Your job is to verify that StretchBot's responses follow the correct protocol and fix any errors.

**WHAT STRETCHBOT SHOULD DO (Main LLM Rules):**

1. **Exercise Status Logic:**
   - If status = "success" → Congratulate user + use "NEXT_EXERCISE: [brief instruction]"
   - If status = "not yet" → Encourage to continue current exercise (NO NEXT_EXERCISE)
   - If user wants to skip or is not able to do this exercise → Allow "NEXT_EXERCISE: [brief instruction]"

2. **Action Prefixes (MUST be used correctly):**
   - "NEXT_EXERCISE: " → Only when moving to next stretch
   - "POINT_<OBJECT>: " → When offering/pointing to a physical object (GLASS, BANANA, COFFEE, etc.) - FORMAT: "POINT_Coffee I think some coffee would help!" (action prefix followed immediately by text)
   - "STOP_ROUTINE: " → Only when ending the entire routine or user wants to stop

3. **Context Awareness:**
   - Read user's emotional/physical state from indirect cues ("I didn't sleep well" = tired)
   - Use knowledge graph to suggest relevant objects (tired → coffee/banana, thirsty → water)
   - Don't repeat offers already refused in dialogue history
   - Respond to user's actual question/concern

4. **Communication Style:**
   - Friendly, brief, empathetic (1-2 sentences max)
   - Not robotic or repetitive
   - Acknowledge user's feelings/state

**YOUR VERIFICATION TASK:**
Check if StretchBot's output violates any of these rules. Common errors to fix:
- Using "NEXT_EXERCISE" when status is "not yet" and user hasn't asked to skip
- Missing action prefixes when needed
- Repeating previously refused offers
- Being too wordy or not empathetic enough
- Ignoring user's emotional/physical state

**Context:**
- Current exercise: {current_exercise}
- Next exercise: {next_exercise}
- Context: {context_description}
- Dialogue history: {history_str}
- Knowledge Graph Context: {kg_context}
**StretchBot's output to verify:**
\"\"\"
{llm1_output}
\"\"\"

**Instructions:**
- If the output is correct, return ONLY the "Output:" section exactly as-is
- If there are errors, fix them while maintaining the empathetic tone
- If NEXT_EXERCISE is incorrectly used, remove it and encourage current exercise instead
- DO NOT copy the original "Reasoning:" section - only provide your verification reasoning
- IMPORTANT: Action prefixes must be on the SAME LINE as the message text (e.g., "POINT_Coffee I think some coffee would help!")

Format your response:

Reasoning: [Brief explanation of what you found and why you corrected it or kept it as-is]

Output: [ONLY the final corrected robot response - action prefix and text on same line, no line breaks between prefix and message]"""

    try:
        response = hf_client.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[{"role": "user", "content": verifier_prompt}],
            max_tokens=500,
            temperature=0.3  # Lower temperature for more consistent verification
        )
        
        return response.choices[0].message.content
            
    except Exception as e:
        print(f"⚠️ Verification error: {e}")
        # If verification fails, return original output
        return llm1_output


# Exemple d'utilisation simple
"""
if __name__ == "__main__":
    # Exemple de variables à remplacer par ton contexte réel
    context_description = "Exercise status: success"
    current_exercise = "Stretch your arms above your head"
    next_exercise = "Touch your toes"
    dialogue_history = [
        "Human: I'm feeling pretty good today!",
        "Robot: Awesome! Let's get started with the stretching."
    ]
    llm1_output = "Great job! Now let's move to the next exercise."

    verifier_reply = verify_with_hf_llm(
        llm1_output,
        context_description=context_description,
        current_exercise=current_exercise,
        next_exercise=next_exercise,
        dialogue_history=dialogue_history
    )
    print(verifier_reply)
    """
