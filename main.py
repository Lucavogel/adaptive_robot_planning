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
from task_monitoring import check_exercise
import cv2
import mediapipe as mp
import threading
import time

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
    "Stretch your arms above your head",
    "Touch your toes",
    "lean left and right",
]
def clean(text):
    return re.sub(r"[^\w\s]", "", text).strip().lower()
def is_question(text):
    text = text.lower()
    return "?" in text or text.startswith(("would", "shall", "do you", "should", "are you", "is it", "did you"))

latest_landmarks = None
current_exercise = None
exercise_success_flag = False  # <-- Ajoute ce flag

stop_event = threading.Event()

def camera_loop(exercise_name, stop_event):
    global latest_landmarks, exercise_success_flag
    current_exercise = exercise_name
    window_name = f"Camera - StretchBot - {current_exercise}"
    print(f"[Camera] Starting camera for: {current_exercise}")
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera failed to open!")
        stop_event.set()  # Signale au main que la caméra n'a pas démarré
        exercise_success_flag = True  # Pour débloquer la boucle d'attente
        return
    print("✅ Camera opened successfully.")
    frame_count = 0
    while not stop_event.is_set():
        if exercise_success_flag:
            break
        success, frame = cap.read()
        frame_count += 1
        if not success:
            print(f"[Camera] Frame {frame_count}: Failed to read frame.")
            latest_landmarks = None
            time.sleep(0.01)
            continue
        else:
            print(f"[Camera] Frame {frame_count}: Read OK.")

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_image)
        if results.pose_landmarks:
            print(f"[Camera] Frame {frame_count}: Landmarks detected.")
            latest_landmarks = results.pose_landmarks.landmark
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp.solutions.drawing_utils.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=3),
                mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2)
            )
        else:
            print(f"[Camera] Frame {frame_count}: No landmarks.")
            latest_landmarks = None

        try:
            from task_monitoring import check_exercise
            if latest_landmarks:
                status = check_exercise(current_exercise, latest_landmarks)
                print(f"[Camera] Frame {frame_count}: Status for '{current_exercise}': {status}")
                if status == "success":
                    message = "Exercice réussi !"
                    color = (0, 255, 0)
                    exercise_success_flag = True
                elif status == "not yet":
                    message = "Continue l'exercice..."
                    color = (0, 0, 255)
                else:
                    message = ""
                    color = (255, 255, 255)
                if message:
                    cv2.putText(
                        frame, message, (30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA
                    )
            else:
                print(f"[Camera] Frame {frame_count}: No landmarks.")
        except Exception as e:
            print(f"[Camera] Exception in check_exercise: {e}")

        cv2.imshow(window_name, frame)
        print(f"[Camera] Frame {frame_count}: imshow called.")
        if cv2.waitKey(1) & 0xFF == 27:
            print("[Camera] ESC pressed, closing window.")
            break

        time.sleep(0.01)

    cap.release()
    print("[Camera] Camera released.")
    cv2.destroyAllWindows()  # <-- Utilise ceci à la place de destroyWindow(window_name)
    print("[Camera] All windows destroyed.")
    time.sleep(1)
    print("[Camera] Camera thread finished.")

def continuous_camera_loop(stop_event):
    global latest_landmarks
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera failed to open!")
        stop_event.set()
        return
    print("✅ Camera opened successfully (continuous mode).")
    while not stop_event.is_set():
        success, frame = cap.read()
        if not success:
            latest_landmarks = None
            time.sleep(0.01)
            continue
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_image)
        if results.pose_landmarks:
            latest_landmarks = results.pose_landmarks.landmark
        else:
            latest_landmarks = None
        # Optionnel : afficher la fenêtre en continu
        cv2.imshow("Pose", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            stop_event.set()
            break
        time.sleep(0.01)
    cap.release()
    cv2.destroyAllWindows()
    print("[Camera] Camera thread finished.")

def main():
    global current_exercise, exercise_success_flag
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
    
    stop_routine = False
    stop_event.clear()
    camera_thread = threading.Thread(target=continuous_camera_loop, args=(stop_event,), daemon=True)
    camera_thread.start()

    for i, exercise in enumerate(exercise_sequence):
        current_exercise = exercise
        exercise_success_flag = False

        print(f"\n➡️ Exercise {i+1}: {exercise}")
        next_exercise = exercise_sequence[i + 1] if i + 1 < len(exercise_sequence) else "None"
        perception_context = get_environment_context_test()
        print(perception_context)
        print("🧍 Say something to the robot (stop talking = end)...")
        human_input = input("You: ")
        if human_input:
            dialogue_history.append(f"Human: {human_input}")

        while True:
            if latest_landmarks:
                status = check_exercise(exercise, latest_landmarks)
                perception_context = f"Exercise status: {status}"
                if status == "success":
                    exercise_success_flag = True
            else:
                perception_context = "No person detected."

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

            if "STOP_ROUTINE" in action:
                print("\n🛑 Routine interrompue par le robot.")
                stop_routine = True
                break
            if "NEXT_EXERCISE:" in action:
                break

            human_input = input("You: ")
            if human_input:
                dialogue_history.append(f"Human: {human_input}")

        if stop_routine:
            break
        
        while not exercise_success_flag:
            time.sleep(0.1)
        time.sleep(0.5)
        print("✅ Passage à l'exercice suivant !")
        
    print("\n✅ Routine terminée.")
    print("\n--- Full Conversation Log ---")
    for line in dialogue_history:
        print(line)

    stop_event.set()
    camera_thread.join()
    commander_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
