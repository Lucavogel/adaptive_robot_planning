import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

def check_exercise(exercise, landmarks):
    if exercise == "Stretch your arms above your head":
        left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
        right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y
        seuil_haut = 0.3
        if left_wrist < left_shoulder and right_wrist < right_shoulder and left_wrist < seuil_haut and right_wrist < seuil_haut:
            return "success"
        
        
        else:
            return "not yet"
    elif exercise == "Touch your toes":
        main_points = [18, 20, 22, 16]
        pied_points = [28, 30, 32]
        seuil_distance = 0.1
        touche_pieds = True
        for idx_main in main_points:
            proche = False
            x_main = landmarks[idx_main].x
            y_main = landmarks[idx_main].y
            for idx_pied in pied_points:
                x_pied = landmarks[idx_pied].x
                y_pied = landmarks[idx_pied].y
                dist = ((x_main - x_pied)**2 + (y_main - y_pied)**2)**0.5
                if dist < seuil_distance:
                    proche = True
                    break
            if not proche:
                touche_pieds = False
                break
        if touche_pieds:
            return "success"
        else:
            return "not yet"
    elif exercise == "lean left and right":
        l_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        r_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        l_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        r_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        shoulders_center_x = (l_shoulder.x + r_shoulder.x) / 2
        hips_center_x = (l_hip.x + r_hip.x) / 2
        seuil_inclinaison = 0.03
        diff = shoulders_center_x - hips_center_x
        if abs(diff) > seuil_inclinaison:
            return "success"
        else:
            return "not yet"
    return "not checked"

if __name__ == "__main__":
    exercise_sequence = [
        "Stretch your arms above your head",
        "Touch your toes",
        "lean left and right",
    ]
    exercise_idx = 0

    cap = cv2.VideoCapture(0)
    while cap.isOpened() and exercise_idx < len(exercise_sequence):
        success, image = cap.read()
        if not success:
            break

        image = cv2.flip(image, 1)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_image)

        message = ""
        color = (255, 255, 255)
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
            )
            # Affiche le numéro de chaque point
            h, w, _ = image.shape
            for idx, landmark in enumerate(results.pose_landmarks.landmark):
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.putText(
                    image, str(idx), (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA
                )

            # Vérifie l'exercice courant
            exercice = exercise_sequence[exercise_idx]
            result = check_exercise(exercice, results.pose_landmarks.landmark)
            if result == "success":
                message = f"✅ {exercice} réussi !"
                color = (0, 255, 0)
                exercise_idx += 1  # Passe à l'exercice suivant
            elif result == "not yet":
                message = f"Fais : {exercice}"
                color = (0, 0, 255)
            else:
                message = ""
                color = (255, 255, 255)

        # Affiche le message et l'exercice courant
        cv2.putText(
            image, message, (30, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA
        )
        if exercise_idx < len(exercise_sequence):
            cv2.putText(
                image, f"Exercice: {exercise_sequence[exercise_idx]}", (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 0), 2, cv2.LINE_AA
            )
        else:
            cv2.putText(
                image, "Routine terminée !", (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2, cv2.LINE_AA
            )

        cv2.imshow("Pose", image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
