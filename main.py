from reasoning import reason_with_context
from reasoning_ollama import reason_with_context_ollama
from planner import extract_action_from_response, clean_llm_response
from perception import get_environment_context_test
from perception import get_environment_context
from speech_to_text import listen_until_silent
from text_to_speech import speak
import re
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time
import cv2
import mediapipe as mp
from task_monitoring import check_exercise
import threading

class LLMCommander(Node):
    def __init__(self):
        super().__init__('llm_commander')
        self.publisher = self.create_publisher(String, 'target_point', 10)

    def send_command(self, command):
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f'Command sent: {command}')

def llm_interaction_thread(exercise, next_exercise, commander_node, stop_flag, dialogue_history, get_status_func, perception_context):
    while not stop_flag['stop']:
        exercise_status = get_status_func()
        context_description = f"Exercise status: {exercise_status}\n{perception_context}"
        print("🧍 Say something to the robot (speak, then stay silent to end)...")
        human_input = listen_until_silent(timeout=1.2)
        #human_input = input("You (text): ")  # For testing purposes, replace with listen_until_silent in production
        if human_input:
            print(f"You (speech): {human_input}")
            dialogue_history.append(f"Human: {human_input}")

        llm_response = reason_with_context(
            context_description,
            current_exercise=exercise,
            next_exercise=next_exercise,
            dialogue_history=dialogue_history
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
        dialogue_history.append(f"Robot: {action}")

        if "STOP_ROUTINE" in action:
            stop_flag['stop'] = True
            break
        if "NEXT_EXERCISE" in action:
            break

def main():
    dialogue_history = []
    rclpy.init()
    commander_node = LLMCommander()

    intro_context = (
        "You are about to start a gentle morning stretching routine with StretchBot. "
        "The robot will guide you step by step. "
        "Take your time, listen to your body, and don't hesitate to ask questions or request a break at any time. "
        "Let's begin together!"
    )
    intro_response = reason_with_context(intro_context, "", exercise_sequence[0])
    print("🤖", intro_response)
    action = extract_action_from_response(intro_response)
    print("✅ Robot Action:", action)
    speak(clean_llm_response(action))
    dialogue_history.append(f"Robot: {action}")
    memory.append(action)

    stop_flag = {"stop": False}

    for i, exercise in enumerate(exercise_sequence):
        if stop_flag["stop"]:
            break

        print(f"\n➡️ Exercise {i+1}: {exercise}")
        next_exercise = exercise_sequence[i + 1] if i + 1 < len(exercise_sequence) else "None"

        print("🧍 Fais l'exercice devant la caméra... (ESC pour quitter)")

        # Get environment context in the main thread (with imshow)
        #perception_context = get_environment_context(show_window=True)
        perception_context = get_environment_context_test()

        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose()
        mp_drawing = mp.solutions.drawing_utils
        cap = cv2.VideoCapture(0)
        status = "not yet"

        def get_status():
            return status

        # Pass perception_context to the LLM thread
        llm_thread = threading.Thread(
            target=llm_interaction_thread,
            args=(exercise, next_exercise, commander_node, stop_flag, dialogue_history, get_status, perception_context)
        )
        llm_thread.start()

        while not stop_flag["stop"] and llm_thread.is_alive():
            success, image = cap.read()
            if not success:
                break
            image = cv2.flip(image, 1)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_image)
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=3),
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                )
                h, w, _ = image.shape
                for idx, landmark in enumerate(results.pose_landmarks.landmark):
                    x, y = int(landmark.x * w), int(landmark.y * h)
                    cv2.putText(image, str(idx), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
                status = check_exercise(exercise, results.pose_landmarks.landmark)
                if status == "success":
                    break

            cv2.imshow(f"Pose_{exercise}", image)
            if cv2.waitKey(5) & 0xFF == 27:
                stop_flag["stop"] = True
                break

        cap.release()
        cv2.destroyAllWindows()
        llm_thread.join()

        if stop_flag["stop"]:
            break

        print("✅ Passage à l'exercice suivant !")
        time.sleep(0.5)

    print("\n✅ Routine terminée.")
    print("\n--- Full Conversation Log ---")
    for line in dialogue_history:
        print(line)

    commander_node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    memory = []
    exercise_sequence = [
        "Stretch your arms above your head",
        "Touch your toes",
        "lean left and right",
    ]
    main()
