from reasoning import reason_with_context
from reasoning_ollama import reason_with_context_ollama
from planner import extract_action_from_response
from perception import get_environment_context
import re
from speech_to_text import listen_until_silent
from text_to_speech import speak

memory = []

exercise_sequence = [
    "Stretch your arms",
    "Touch your toes",
    "Rotate your neck",
    "stretching session finished"
]
def clean(text):
    return re.sub(r"[^\w\s]", "", text).strip().lower()
def is_question(text):
    text = text.lower()
    return "?" in text or text.startswith(("would", "shall", "do you", "should", "are you", "is it", "did you"))
def main():
    dialogue_history = []

    # Add a welcome message at the start
    welcome_message = "Robot: Hello! Welcome to the stretching routine. I'm here to guide you. Let's have a great session together!"
    print(welcome_message)
    dialogue_history.append(welcome_message)

    for i, exercise in enumerate(exercise_sequence):
        print(f"\n➡️ Exercise {i+1}: {exercise}")

        # Prochaine étape
        next_exercise = exercise_sequence[i + 1] if i + 1 < len(exercise_sequence) else "None"

        # Intro du robot
        robot_intro = f"Robot: Let's start with the next exercise: {exercise}."
        print(robot_intro)
        dialogue_history.append(robot_intro)

        # Premier message de l’humain
        print("🧍 Say something to the robot (stop talking = end)...")
        human_input = listen_until_silent()
        
        if human_input:
            print(f"\nYou: {human_input}")
            dialogue_history.append(f"Human: {human_input}")

        while True:
            context_description = get_environment_context() + "\n" + "\n".join(dialogue_history)

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

            # Sinon, on continue la conversationco
            print("🧍 Say something to the robot (stop talking = end)...")
            human_input = listen_until_silent()
            
            if human_input:
                print(f"\nYou: {human_input}")
                dialogue_history.append(f"Human: {human_input}")        
    print("\n✅ Routine terminée.")
    print("\n--- Full Conversation Log ---")
    for line in dialogue_history:
        print(line)



if __name__ == "__main__":
    main()
