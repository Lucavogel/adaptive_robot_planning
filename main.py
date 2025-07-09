import re
import time
import threading
import queue

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import cv2
import mediapipe as mp
from verification_loop import verify_with_hf_llm  # ta fonction de vérification avec LLM
from task_monitoring import check_exercise  # ta fonction avec timers
from reasoning import reason_with_context
from planner import extract_action_from_response, clean_llm_response
from perception import get_environment_context_test
from speech_to_text import listen_until_silent
from text_to_speech import speak, speak_text_realistic
emotion = "happy"  # Par défaut, on utilise une émotion neutre

class LLMCommander(Node):
    def __init__(self):
        super().__init__('llm_commander')
        self.publisher = self.create_publisher(String, 'target_point', 10)

    def send_command(self, command):
        msg = String()
        msg.data = command
        self.publisher.publish(msg)
        self.get_logger().info(f'Command sent: {command}')


def llm_interaction_thread(exercise, next_exercise, commander_node, stop_flag, dialogue_history, get_status_func, perception_context, state):
    while not stop_flag['stop']:
        audio_queue = queue.Queue()
        listening_done = threading.Event()

        def listening_task():
            text = listen_until_silent(timeout=1)
            audio_queue.put(text)
            listening_done.set()

        thread = threading.Thread(target=listening_task)
        thread.start()
        listening_done.wait()

        try:
            human_input = audio_queue.get_nowait()
        except queue.Empty:
            human_input = ""

        latest_status = get_status_func()
        
        # Récupération temps (diff selon l'exercice)
        if exercise == "lean left and right":
            current_time_left = state.get("held_time_left", 0.0)
            current_time_right = state.get("held_time_right", 0.0)
            time_info = f"Current hold times: Left {current_time_left:.1f}s, Right {current_time_right:.1f}s"
        else:
            current_time = state.get("held_time", 0.0)
            time_info = f"Current hold time: {current_time:.1f}s"

        context_description = f"Exercise status: {latest_status}\n{time_info}\n{perception_context}"

        if human_input:
            print(f"You (speech): {human_input}")
            dialogue_history.append(f"Human: {human_input}")

        if human_input or latest_status == "success":
            llm_response = reason_with_context(
                context_description,
                current_exercise=exercise,
                next_exercise=next_exercise,
                dialogue_history=dialogue_history
            )
            
            
            
            print("\n🤖 Robot's reasoning:\n", llm_response)
            action = extract_action_from_response(llm_response)
            print("✅ Robot Action:", action)
            from gradio_client import Client
            from playsound import playsound

            # 1. Appel API


            """
            verifier_reply = verify_with_hf_llm(
            action,
            context_description=context_description,
            current_exercise=exercise,
            next_exercise=next_exercise,
            dialogue_history=dialogue_history
            )
            print("\n🔍 Verifier's response:\n", verifier_reply)
            """
            if "POINT_" in action:
                match = re.search(r"(POINT_[A-Z_]+)", action)
                if match:
                    point_name = match.group(1)
                    commander_node.send_command(point_name)

            clean_action = clean_llm_response(action)
            #speak(clean_action)
            speak_text_realistic(clean_action, voice="alloy", emotion = emotion)

            dialogue_history.append(f"Robot: {action}")

            if "STOP_ROUTINE" in action:
                stop_flag['stop'] = True
                break
            if "NEXT_EXERCISE" in action:
                break



def main():
    exercise_sequence = [
        "Stretch your arms above your head",
        "Touch your toes",
        "lean left and right",
    ]
    exercise_idx = 0
    state = {
    "held_time": 0.0,
    "last_valid_time": 0,
    "held_time_left": 0.0,
    "held_time_right": 0.0,
    "last_valid_left": 0,
    "last_valid_right": 0
    }

    dt = 1.0 / 30.0  # approx 30 fps

    rclpy.init()
    commander_node = LLMCommander()

    dialogue_history = []
    stop_flag = {"stop": False}

    # Optionnel, intro
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
    clean_action = clean_llm_response(action)
    speak_text_realistic(clean_action, voice="alloy", emotion=emotion)


    #speak(clean_llm_response(action))
    dialogue_history.append(f"Robot: {action}")

    perception_context = get_environment_context_test()

    cap = cv2.VideoCapture(0)

    while cap.isOpened() and exercise_idx < len(exercise_sequence) and not stop_flag["stop"]:
        exercice = exercise_sequence[exercise_idx]
        next_exercise = exercise_sequence[exercise_idx + 1] if exercise_idx + 1 < len(exercise_sequence) else "None"
        status = "not yet"

        def get_status():
            return status

        # Start LLM thread per exercise
        llm_thread = threading.Thread(
            target=llm_interaction_thread,
            args=(exercice, next_exercise, commander_node, stop_flag, dialogue_history, get_status, perception_context, state)
        )
        llm_thread.start()

        while cap.isOpened() and not stop_flag["stop"]:
            success, image = cap.read()
            if not success:
                break

            image = cv2.flip(image, 1)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_image)

            if results.pose_landmarks:
                status, state = check_exercise(exercice, results.pose_landmarks.landmark, state, dt)

                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=3),
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                )

                if exercice == "lean left and right":
                    cv2.putText(image, f"Lean Left: {state['held_time_left']:.1f}s", (30, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 0, 200), 2)
                    cv2.putText(image, f"Lean Right: {state['held_time_right']:.1f}s", (30, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 100, 255), 2)
                else:
                    cv2.putText(image, f"Hold: {state['held_time']:.1f}s", (30, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

                if status == "success":
                    exercise_idx += 1
                    state = {
                        "held_time": 0.0,
                        "last_valid_time": 0,
                        "held_time_left": 0.0,
                        "held_time_right": 0.0,
                        "last_valid_left": 0,
                        "last_valid_right": 0
                    }
                    break

            if exercise_idx < len(exercise_sequence):
                cv2.putText(image, f"Exercice: {exercise_sequence[exercise_idx]}", (30, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 0), 2)
            else:
                cv2.putText(image, "Routine terminée !", (30, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2)

            cv2.imshow("Pose", image)
            if cv2.waitKey(5) & 0xFF == 27:
                stop_flag["stop"] = True
                break

        llm_thread.join()

    cap.release()
    cv2.destroyAllWindows()

    print("\n✅ Routine terminée.")
    print("\n--- Full Conversation Log ---")
    for line in dialogue_history:
        print(line)

    commander_node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    mp_drawing = mp.solutions.drawing_utils

    main()
