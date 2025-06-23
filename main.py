from reasoning import reason_with_context
from reasoning_ollama import reason_with_context_ollama
from planner import extract_action_from_response
from perception import get_environment_context
from perception import get_environment_context_test
import re
from speech_to_text import listen_until_silent
from text_to_speech import speak

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

    intro_prompt = (
    "You are StretchBot, a friendly robot coach. "
    "Please introduce yourself and the stretching routine to the user in a warm, personalized way. "
    "Mention the exercises: " + ", ".join(exercise_sequence[:-1]) + "."
)
    intro_response = reason_with_context(
    context_description="",
    current_exercise="",
    next_exercise=exercise_sequence[0]
)

    print("🤖", intro_response)
    action = extract_action_from_response(intro_response)
    print("✅ Robot Action:", action)
    speak(action)
    dialogue_history.append(f"Robot: {action}")
    memory.append(action)
    
    for i, exercise in enumerate(exercise_sequence):
        print(f"\n➡️ Exercise {i+1}: {exercise}")

        # Prochaine étape
        next_exercise = exercise_sequence[i + 1] if i + 1 < len(exercise_sequence) else "None"

        # --- NOUVEAU : Prendre une image et détecter les objets ---
        #perception_context = get_environment_context(show_window=True)
        perception_context = get_environment_context_test()  # For testing purposes
        print(perception_context)
        # ----------------------------------------------------------


        # Premier message de l’humain
        print("🧍 Say something to the robot (stop talking = end)...")
        #human_input = listen_until_silent()
        human_input = input("You: ")
        
        if human_input:
            #print(f"\nYou: {human_input}")
            dialogue_history.append(f"Human: {human_input}")

        while True:
            # --- Utilise la perception dans le contexte ---
            context_description = perception_context + "\n" + "\n".join(dialogue_history)
            # ----------------------------------------------

            # Appel LLM
            llm_response = reason_with_context(
                context_description,
                current_exercise=exercise,
                next_exercise=next_exercise
            )
            print("\n🤖 Robot's reasoning:\n", llm_response)

            # Extraction de l’action
            action = extract_action_from_response(llm_response)
            print("✅ Robot Action:", action)
            speak(action)
            memory.append(action)
            dialogue_history.append(f"Robot: {action}")

            # Nouvelle logique : détection explicite du passage à l'exercice suivant
            
            if "NEXT_EXERCISE:" in action:
                break

            # Sinon, on continue la conversation
            #print("🧍 Say something to the robot (stop talking = end)...")
            #human_input = listen_until_silent()
            human_input = input("You: ")
            if human_input:
                #print(f"\nYou: {human_input}")
                dialogue_history.append(f"Human: {human_input}")        
    print("\n✅ Routine terminée.")
    print("\n--- Full Conversation Log ---")
    for line in dialogue_history:
        print(line)

    outro_prompt = (
    "You are StretchBot, a friendly robot coach. "
    "The user has just finished all their stretching exercises. "
    "Congratulate them in a warm, personalized way and encourage them for the rest of their day."
)
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
