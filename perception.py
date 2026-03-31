from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")  

def get_environment_context(frame, show_window=True):
    if frame is None:
        return "- The robot sees: nothing (no image provided)."

   
    results = model(frame)
    detected = set()

    
    annotated_frame = frame.copy()
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            detected.add(label)
            
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            cv2.rectangle(annotated_frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0,255,0), 2)
            cv2.putText(annotated_frame, label, (xyxy[0], xyxy[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)

   
    print("Detected objects:", ", ".join(detected) if detected else "None")

    if show_window:
        cv2.imshow("YOLO Detection", annotated_frame)
        cv2.waitKey(2000)
        cv2.destroyAllWindows()

    return list(detected)

def get_environment_context_test():

    return (
        "GlassOfWater, Towel, Banana, Coffee, Chair"
    )
import time
from collections import deque
import cv2
from deepface import DeepFace

def detect_emotion_print():
    cap = cv2.VideoCapture(0)
    print("Appuie sur Ctrl+C pour arrêter")

    last_analysis_time = 0
    emotion_buffer = deque(maxlen=5) 

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

                   
                    most_common_emotion = max(set(emotion_buffer), key=emotion_buffer.count)
                    print(f"Emotion détectée (stabilisée) : {most_common_emotion}")

                    last_analysis_time = current_time
                except Exception as e:
                    print("Erreur DeepFace:", e)

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nArrêt demandé par utilisateur")

    cap.release()

