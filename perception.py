from ultralytics import YOLO
import cv2

def get_environment_context(show_window=True):
    # Charger le modèle YOLO pré-entraîné (par exemple, yolov8n.pt)
    model = YOLO("yolov8n.pt")  # Téléchargé automatiquement si absent

    # Ouvre la webcam
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return "- The robot sees: nothing (camera error)."

    # Détection d'objets
    results = model(frame)
    detected = set()

    # Annoter l'image avec les détections
    annotated_frame = frame.copy()
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            detected.add(label)
            # Dessiner la boîte et le label
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            cv2.rectangle(annotated_frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0,255,0), 2)
            cv2.putText(annotated_frame, label, (xyxy[0], xyxy[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

    # Print detected objects
    print("Detected objects:", ", ".join(detected) if detected else "None")

    if show_window:
        cv2.imshow("YOLO Detection", annotated_frame)
        cv2.waitKey(2000)  # Affiche 2 secondes
        cv2.destroyAllWindows()

    if detected:
        obj_list = ", ".join(detected)
        return f"- The robot sees: {obj_list}."
    else:
        return "- The robot sees: nothing."

def get_environment_context_test():

    return (
        "- The robot sees: a glass of water , a towel, and a banana."
    )
import time
from collections import deque
import cv2
from deepface import DeepFace

def detect_emotion_print():
    cap = cv2.VideoCapture(0)
    print("Appuie sur Ctrl+C pour arrêter")

    last_analysis_time = 0
    emotion_buffer = deque(maxlen=5)  # mémorise les 5 dernières émotions

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erreur de capture caméra")
                break

            current_time = time.time()
            if current_time - last_analysis_time > 2:
                try:
                    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                    emotion = result[0]['dominant_emotion']
                    emotion_buffer.append(emotion)

                    # Trouve l'émotion la plus fréquente sur la fenêtre glissante
                    most_common_emotion = max(set(emotion_buffer), key=emotion_buffer.count)
                    print(f"Emotion détectée (stabilisée) : {most_common_emotion}")

                    last_analysis_time = current_time
                except Exception as e:
                    print("Erreur DeepFace:", e)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nArrêt demandé par utilisateur")

    cap.release()

