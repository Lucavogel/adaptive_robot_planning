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

    if show_window:
        cv2.imshow("YOLO Detection", annotated_frame)
        cv2.waitKey(2000)  # Affiche 2 secondes
        cv2.destroyAllWindows()

    if detected:
        obj_list = ", ".join(detected)
        return f"- The robot sees: {obj_list}."
    else:
        return "- The robot sees: nothing."
"""
def get_environment_context():

    return (
        "- The robot sees: a glass of water , a towel, and a banana."
    )
"""