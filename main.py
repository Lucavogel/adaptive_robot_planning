from reasoning import reason_with_context
from reasoning_ollama import reason_with_context_ollama
from planner import extract_action_from_response
from perception import get_environment_context
from perception import get_environment_context_test
import re
from speech_to_text import listen_until_silent
from text_to_speech import speak
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from planner import clean_llm_response

class LLMCommander(Node):
    def __init__(self):
        super().__init__('llm_commander')
        self.publisher = self.create_publisher(String, 'target_point', 10)

    def send_command(self, command):
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f'Command sent: {command}')

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
    rclpy.init()
    commander_node = LLMCommander()


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
    action = clean_llm_response(action)
    speak(action)
    dialogue_history.append(f"Robot: {action}")
    memory.append(action)
    
    stop_routine = False  # Ajoute ce flag avant la boucle for

    for i, exercise in enumerate(exercise_sequence):
        print(f"\n➡️ Exercise {i+1}: {exercise}")
        next_exercise = exercise_sequence[i + 1] if i + 1 < len(exercise_sequence) else "None"
        perception_context = get_environment_context_test()
        print(perception_context)
        print("🧍 Say something to the robot (stop talking = end)...")
        human_input = input("You: ")
        if human_input:
            dialogue_history.append(f"Human: {human_input}")

        while True:
            context_description = perception_context + "\n" + "\n".join(dialogue_history)
            llm_response = reason_with_context(
                context_description,
                current_exercise=exercise,
                next_exercise=next_exercise
            )
            print("\n🤖 Robot's reasoning:\n", llm_response)
            action = extract_action_from_response(llm_response)
            print("✅ Robot Action:", action)
            
            if "POINT_" in action:
                match = re.search(r"(POINT_[A-Z_]+)", action)
                if match:
                    point_name = match.group(1)
                    commander_node.send_command(point_name)
            clean_action = clean_llm_response(action)
            speak(clean_action)
            memory.append(action)
            dialogue_history.append(f"Robot: {action}")

            # Nouvelle logique : détection explicite du passage à l'exercice suivant
            if "STOP_ROUTINE" in action:
                print("\n🛑 Routine interrompue par le robot.")
                stop_routine = True   # Active le flag
                break  # Sort de la boucle while
            if "NEXT_EXERCISE:" in action:
                break

            human_input = input("You: ")
            if human_input:
                dialogue_history.append(f"Human: {human_input}")

        if stop_routine:   # Ajoute ce test juste après la boucle while
            break
        
    print("\n✅ Routine terminée.")
    print("\n--- Full Conversation Log ---")
    for line in dialogue_history:
        print(line)

    commander_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
