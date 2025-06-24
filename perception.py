#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from ultralytics import YOLO

bridge = CvBridge()
model = YOLO("yolov8n.pt")  # 🧠 Remplace par ton modèle si besoin

# 🧠 Variable globale pour objets détectés
latest_detected_objects = set()

def image_callback(msg):
    global latest_detected_objects
    try:
        # Convertir ROS → OpenCV
        frame = bridge.imgmsg_to_cv2(msg, "bgr8")
        results = model(frame)
        detected = set()

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                detected.add(label)

        latest_detected_objects = detected
        print("📸 Objets détectés:", ", ".join(detected) if detected else "aucun")

    except Exception as e:
        print("⚠️ Erreur vision:", e)

def get_environment_context():
    """
    Initialise ROS, écoute les images pendant quelques secondes, retourne la description des objets détectés.
    """
    global latest_detected_objects
    rospy.init_node("perception_node", anonymous=True)
    rospy.Subscriber("/usb_cam/image_raw", Image, image_callback)

    timeout = rospy.Time.now() + rospy.Duration(5.0)
    rate = rospy.Rate(10)

    while not rospy.is_shutdown() and rospy.Time.now() < timeout:
        if latest_detected_objects:
            break
        rate.sleep()

    if latest_detected_objects:
        return f"- The robot sees: {', '.join(latest_detected_objects)}."
    else:
        return "- The robot sees: nothing."
