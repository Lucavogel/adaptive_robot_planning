#!/usr/bin/env python3


from reasoning import reason_with_context
from planner import extract_action_from_response
from perception import get_environment_context
from speech_to_text import listen_until_silent
from text_to_speech import speak
from plan_and_execute import execute_llm_decision
import re

# Mémoire et séquence d'exercices
memory = []
exercise_sequence = [
    "Stretch your arms",
    "Touch your toes",
    "Rotate your neck"
]

def clean(text):
    return re.sub(r"[^\w\s]", "", text).strip().lower()

def is_question(text):
    text = text.lower()
    return "?" in text or text.startswith(("would", "shall", "do you", "should", "are you", "is it", "did you"))

def main():
    dialogue_history = []

    # 🟢 Introduction
    intro_response = reason_with_context(
        context_description="",
        current_exercise="",
        next_exercise=exercise_sequence[0]
    )

    print("🤖", intro_response)
    action = extract_action_from_response(intro_response)
    speak(action)
    memory.append(action)
    dialogue_history.append(f"Robot: {action}")

    # 🔁 Boucle d'exercices
    for i, exercise in enumerate(exercise_sequence):
        print(f"\n➡️ Exercise {i+1}: {exercise}")
        next_exercise = exercise_sequence[i + 1] if i + 1 < len(exercise_sequence) else "None"

        # 📷 Perception simulée
        perception_context = get_environment_context()
        print(perception_context)

        # 🧍 Message de l’humain
        print("🧍 Say something to the robot...")
        # human_input = listen_until_silent()
        human_input = input("You: ")
        if human_input:
            print(f"\nYou: {human_input}")
            dialogue_history.append(f"Human: {human_input}")

        # 🔁 Interaction jusqu'à l'exercice suivant
        while True:
            context_description = perception_context + "\n" + "\n".join(dialogue_history)
            llm_response = reason_with_context(
                context_description,
                current_exercise=exercise,
                next_exercise=next_exercise
            )
            print("\n🤖 Robot's reasoning:\n", llm_response)

            # 🦾 Exécution éventuelle du mouvement
            execute_llm_decision(llm_response)

            # 🗣️ Action parlée (sans POINT_XXX)
            action = extract_action_from_response(llm_response)
            print("✅ Robot Action:", action)
            spoken_text = re.sub(r"POINT_[A-Z]+\b", "", action).strip()
            speak(spoken_text)

            memory.append(action)
            dialogue_history.append(f"Robot: {action}")

            # Passage à l'exercice suivant ?
            if "NEXT_EXERCISE:" in action:
                break

            # 🧍 Nouvelle entrée utilisateur
            # human_input = listen_until_silent()
            human_input = input("You: ")
            if human_input:
                dialogue_history.append(f"Human: {human_input}")

    # 🎉 Fin de routine
    print("\n✅ Routine terminée.")
    print("\n--- Full Conversation Log ---")
    for line in dialogue_history:
        print(line)

    # 🎤 Message final
    outro_response = reason_with_context(
        context_description="\n".join(dialogue_history),
        current_exercise="",
        next_exercise=""
    )
    print("🤖", outro_response)
    speak(outro_response)
    dialogue_history.append(f"Robot: {outro_response}")

if __name__ == "__main__":
    main()
