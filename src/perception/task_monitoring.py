import cv2
import mediapipe as mp
import time

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

import math
import mediapipe as mp

mp_pose = mp.solutions.pose

import math
import time
import mediapipe as mp

mp_pose = mp.solutions.pose

import math
import time
import mediapipe as mp

mp_pose = mp.solutions.pose

def check_exercise(exercise, landmarks, state, dt=0.033):
    tolerance_reset = 40.0 

    def update_timers(direction=None):
        now = time.time()
        if exercise == "lean left and right":
            if direction == "left":
                state["held_time_left"] = min(state.get("held_time_left", 0) + dt, 5.0)
                state["last_valid_left"] = now
            elif direction == "right":
                state["held_time_right"] = min(state.get("held_time_right", 0) + dt, 5.0)
                state["last_valid_right"] = now
        else:
            state["held_time"] = min(state.get("held_time", 0) + dt, 5.0)
            state["last_valid_time"] = now

    def reset_if_timed_out():
        now = time.time()
        if exercise == "lean left and right":
            last_left = state.get("last_valid_left", 0)
            if last_left != 0 and (now - last_left) > tolerance_reset:
                state["held_time_left"] = 0.0
                state["last_valid_left"] = 0
            last_right = state.get("last_valid_right", 0)
            if last_right != 0 and (now - last_right) > tolerance_reset:
                state["held_time_right"] = 0.0
                state["last_valid_right"] = 0
        else:
            last = state.get("last_valid_time", 0)
            if last != 0 and (now - last) > tolerance_reset:
                state["held_time"] = 0.0
                state["last_valid_time"] = 0

    def is_arms_stretched(landmarks):
        
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
        right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
        nose = landmarks[mp_pose.PoseLandmark.NOSE.value]

     
        left_above = left_wrist.y < nose.y
        right_above = right_wrist.y < nose.y

      
        left_elbow_above = left_elbow.y < nose.y
        right_elbow_above = right_elbow.y < nose.y

       
        wrist_dist = abs(left_wrist.x - right_wrist.x)
        near_center = wrist_dist < 0.3  

        return left_above and right_above and left_elbow_above and right_elbow_above and near_center

    def is_touching_toes_simple(landmarks):
        main_points = [
            mp_pose.PoseLandmark.LEFT_WRIST.value,
            mp_pose.PoseLandmark.RIGHT_WRIST.value,
        ]
        pied_points = [
            mp_pose.PoseLandmark.LEFT_ANKLE.value,
            mp_pose.PoseLandmark.RIGHT_ANKLE.value
        ]

        seuil_distance = 0.4  

        for idx_main in main_points:
            main = landmarks[idx_main]
            for idx_pied in pied_points:
                pied = landmarks[idx_pied]
                dist = ((main.x - pied.x)**2 + (main.y - pied.y)**2)**0.5
                if dist < seuil_distance:
                    return True
        return False

    def detect_lean_direction(landmarks):
        l_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        r_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        l_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        r_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]

      
        shoulder_x = (l_shoulder.x + r_shoulder.x) / 2
        shoulder_y = (l_shoulder.y + r_shoulder.y) / 2
        hip_x = (l_hip.x + r_hip.x) / 2
        hip_y = (l_hip.y + r_hip.y) / 2

     
        dx = shoulder_x - hip_x
        dy = hip_y - shoulder_y  

        angle_rad = math.atan2(dx, dy)
        angle_deg = math.degrees(angle_rad)

        seuil = 15  

        if angle_deg > seuil:
            return "right"
        elif angle_deg < -seuil:
            return "left"
        else:
            return None

    reset_if_timed_out()

    if exercise == "Stretch your arms above your head for 5 seconds":
        if is_arms_stretched(landmarks):
            update_timers()
        return ("success" if state.get("held_time", 0) >= 5.0 else "not yet"), state

    elif exercise == "Touch your toes for 5 seconds":
        if is_touching_toes_simple(landmarks):
            update_timers()
        return ("success" if state.get("held_time", 0) >= 5.0 else "not yet"), state

    elif exercise == "Lean left and right for 5 seconds on each side":
        direction = detect_lean_direction(landmarks)
        if direction in ["left", "right"]:
            update_timers(direction)
        # Pas de reset ici, géré par reset_if_timed_out()

        if state.get("held_time_left", 0) >= 5.0 and state.get("held_time_right", 0) >= 5.0:
            return "success", state
        else:
            return "not yet", state

    return "not checked", state



if __name__ == "__main__":
    exercise_sequence = [
        "Stretch your arms above your head for 5 seconds",
        "Touch your toes for 5 seconds",
        "Lean left and right for 5 seconds on each side",
    ]
    exercise_idx = 0

    # Initial state
    state = {
        "held_time": 0.0,
        "last_valid_time": 0,
        "held_time_left": 0.0,
        "held_time_right": 0.0,
        "last_valid_left": 0,
        "last_valid_right": 0
    }

    cap = cv2.VideoCapture(0)
    while cap.isOpened() and exercise_idx < len(exercise_sequence):
        success, image = cap.read()
        if not success:
            break

        image = cv2.flip(image, 1)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_image)

        dt = 1.0 / 30.0
        message = ""
        color = (255, 255, 255)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2),
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
            )

            exercise = exercise_sequence[exercise_idx]
            result, state = check_exercise(exercise, results.pose_landmarks.landmark, state, dt)

            if result == "success":
                message = f"{exercise} réussi !"
                color = (0, 255, 0)
                exercise_idx += 1
                state = {
                    "held_time": 0.0,
                    "last_valid_time": 0,
                    "held_time_left": 0.0,
                    "held_time_right": 0.0,
                    "last_valid_left": 0,
                    "last_valid_right": 0
                }
            else:
                message = f"Fais : {exercise}"
                color = (0, 0, 255)

   
        cv2.putText(image, message, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        if exercise_idx < len(exercise_sequence):
            current_exercise = exercise_sequence[exercise_idx]
            cv2.putText(image, f"Exercice: {current_exercise}", (30, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 0), 2)

            if current_exercise == "lean left and right":
                cv2.putText(image, f"Lean Left: {state.get('held_time_left', 0):.1f} / 5s",
                            (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 150, 255), 2)
                cv2.putText(image, f"Lean Right: {state.get('held_time_right', 0):.1f} / 5s",
                            (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 150, 255), 2)
            else:
                cv2.putText(image, f"Maintiens encore {max(0, 5.0 - state.get('held_time', 0)):.1f}s",
                            (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 150, 255), 2)
        else:
            cv2.putText(image, "Routine terminée !", (30, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2)

        cv2.imshow("Pose", image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
