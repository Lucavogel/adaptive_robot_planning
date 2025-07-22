#!/usr/bin/env python3

import rospy
import cv2
import numpy as np
from ultralytics import YOLO
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import String
import json
import time

class DetectionSubscriber:
    def __init__(self):
        self.latest_objects = []
        self.latest_aruco_data = []
        self.complete_objects_data = []
        self.last_update = 0
        self.subscriber = rospy.Subscriber('/detected_objects', String, self.detection_callback)
        rospy.loginfo("Subscribed to detection topic")
    
    def detection_callback(self, msg):
        try:
            data = json.loads(msg.data)
            
            # Extraire les objets
            if 'objects' in data:
                self.latest_objects = [obj['name'] for obj in data['objects']]
                self.complete_objects_data = data['objects']
            else:
                self.latest_objects = []
                self.complete_objects_data = []
            
            # Extraire les données ArUco
            if 'aruco_markers' in data:
                self.latest_aruco_data = data['aruco_markers']
            else:
                self.latest_aruco_data = []
                
            self.last_update = time.time()
        except json.JSONDecodeError:
            rospy.logwarn("Failed to parse detection data")

class CameraDetectionNode:
    def __init__(self):
        rospy.init_node("camera_detection_node", anonymous=True)
        
        # Configuration
        self.model = YOLO('yolov8n.pt')
        self.bridge = CvBridge()
        self.frame_count = 0
        
        # ArUco data
        self.latest_aruco_data = []
        
        # Publishers/Subscribers
        self.detection_pub = rospy.Publisher("/detected_objects", String, queue_size=10)
        self.image_sub = rospy.Subscriber("/usb_cam/image_raw", Image, self.image_callback)
        self.aruco_sub = rospy.Subscriber("/aruco_detections", String, self.aruco_callback)
        
        rospy.loginfo("Camera Detection Node with ArUco integration initialized")

    def aruco_callback(self, msg):
        """Callback pour recevoir les données ArUco"""
        try:
            data = json.loads(msg.data)
            if 'markers' in data:
                self.latest_aruco_data = data['markers']
            else:
                self.latest_aruco_data = []
        except json.JSONDecodeError:
            rospy.logwarn("Failed to parse ArUco data")
            self.latest_aruco_data = []

    def find_smallest_bbox_containing_aruco(self, aruco_marker, detected_objects):
        """Trouve la plus petite bounding box qui contient l'ArUco"""
        if "corners" not in aruco_marker:
            return None
        
        # Calculer le centre de l'ArUco
        corners = aruco_marker["corners"][0]
        center_x = sum(corner[0] for corner in corners) / 4
        center_y = sum(corner[1] for corner in corners) / 4
        
        smallest_area = float('inf')
        best_object = None
        
        for obj in detected_objects:
            x1, y1, x2, y2 = obj['bbox']
            
            # Tester si le centre ArUco est dans cette box
            if x1 < center_x < x2 and y1 < center_y < y2:
                area = (x2 - x1) * (y2 - y1)
                
                if area < smallest_area:
                    smallest_area = area
                    best_object = obj
        
        return best_object

    def image_callback(self, msg):
        self.frame_count += 1
        
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")  # Corrigé: bgr8
        except Exception as e:
            rospy.logerr(f"Error converting image: {e}")
            return

        # Détection YOLO
        results = self.model(frame, verbose=False)
        detected_objects = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = self.model.names[class_id]
                    
                    if confidence > 0.5:
                        object_data = {
                            'name': class_name,
                            'confidence': float(confidence),
                            'bbox': [float(x1), float(y1), float(x2), float(y2)],
                            'center_2d': [float((x1 + x2) / 2), float((y1 + y2) / 2)]
                        }
                        detected_objects.append(object_data)

        # Association ArUco -> Objets (NOUVELLE LOGIQUE)
        for aruco_marker in self.latest_aruco_data:
            associated_object = self.find_smallest_bbox_containing_aruco(aruco_marker, detected_objects)
            
            if associated_object:
                associated_object['aruco_marker'] = {
                    "id": aruco_marker["id"],
                    "dictionary": aruco_marker["dictionary"],
                    "corners": aruco_marker["corners"]
                }
                print(f"✅ ArUco {aruco_marker['id']} associé à {associated_object['name']}")
                
                # DEBUG: Afficher le mapping pour verification
                rospy.loginfo(f"🎯 MAPPING DEBUG: ArUco {aruco_marker['id']} → Objet '{associated_object['name']}'")

        # Dessiner et publier
        self.draw_detections(frame, detected_objects)
        self.publish_detections(detected_objects)
        
        cv2.imshow("Object Detection + ArUco", frame)
        cv2.waitKey(1)

    def draw_detections(self, frame, detected_objects):
        """Dessiner les détections sur l'image"""
        for obj in detected_objects:
            x1, y1, x2, y2 = obj['bbox']
            
            # Couleur selon présence ArUco
            color = (0, 255, 0) if obj.get('aruco_marker') else (255, 0, 0)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            
            # Label
            label = f"{obj['name']}: {obj['confidence']:.2f}"
            if obj.get('aruco_marker'):
                label += f" + ArUco {obj['aruco_marker']['id']}"
            
            cv2.putText(frame, label, (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def publish_detections(self, detected_objects):
        """Publication des détections"""
        detection_msg = String()
        detection_msg.data = json.dumps({
            'objects': detected_objects,
            'aruco_markers': self.latest_aruco_data,
            'frame_id': self.frame_count,
            'timestamp': rospy.Time.now().to_sec()
        })
        
        self.detection_pub.publish(detection_msg)
        
        # Log
        if self.frame_count % 30 == 0:
            if detected_objects:
                obj_summary = []
                for obj in detected_objects[:3]:
                    if obj.get('aruco_marker'):
                        obj_summary.append(f"{obj['name']}+ArUco{obj['aruco_marker']['id']}")
                    else:
                        obj_summary.append(f"{obj['name']} (no ArUco)")
                rospy.loginfo(f"Frame {self.frame_count}: {' | '.join(obj_summary)}")

# Global subscriber instance
detection_subscriber = None

def get_environment_context():
    """Get current environment context (non-blocking)"""
    global detection_subscriber
    if detection_subscriber is None:
        detection_subscriber = DetectionSubscriber()
        rospy.sleep(0.5)  # Give time to establish connection
    
    context_parts = []
    
    # Objets détectés
    if detection_subscriber.latest_objects:
        objects_str = ", ".join(set(detection_subscriber.latest_objects))
        context_parts.append(f"- The robot sees: {objects_str}")
    else:
        context_parts.append("- The robot sees: nothing")
    
    # Marqueurs ArUco détectés
    if detection_subscriber.latest_aruco_data:
        aruco_str = ", ".join([f"ArUco {marker['id']}" for marker in detection_subscriber.latest_aruco_data])
        context_parts.append(f"- ArUco markers detected: {aruco_str}")
    
    return "\n".join(context_parts)

def get_latest_objects():
    """Get list of currently detected objects"""
    global detection_subscriber
    if detection_subscriber is None:
        detection_subscriber = DetectionSubscriber()
        rospy.sleep(0.5)
    
    return detection_subscriber.latest_objects.copy()

def get_latest_aruco_data():
    """Get list of currently detected ArUco markers"""
    global detection_subscriber
    if detection_subscriber is None:
        detection_subscriber = DetectionSubscriber()
        rospy.sleep(0.5)
    
    return detection_subscriber.latest_aruco_data.copy()

def get_objects_with_aruco():
    """Get objects that have associated ArUco markers"""
    global detection_subscriber
    if detection_subscriber is None:
        detection_subscriber = DetectionSubscriber()
        rospy.sleep(0.5)
    
    return [obj for obj in detection_subscriber.complete_objects_data if obj.get('aruco_marker')]

if __name__ == '__main__':
    try:
        CameraDetectionNode()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    cv2.destroyAllWindows()