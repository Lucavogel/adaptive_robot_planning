#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import json
import time

class DetectionSubscriber:
    def __init__(self):
        self.latest_objects = []
        self.latest_aruco_data = []
        self.last_update = 0
        self.subscriber = rospy.Subscriber('/detected_objects', String, self.detection_callback)
        rospy.loginfo("Subscribed to detection topic")
    
    def detection_callback(self, msg):
        try:
            data = json.loads(msg.data)
            
            # Extraire les objets
            if 'objects' in data:
                self.latest_objects = [obj['name'] for obj in data['objects']]
            else:
                self.latest_objects = []
            
            # Extraire les données ArUco
            if 'aruco_markers' in data:
                self.latest_aruco_data = data['aruco_markers']
            else:
                self.latest_aruco_data = []
                
            self.last_update = time.time()
        except json.JSONDecodeError:
            rospy.logwarn("Failed to parse detection data")

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
    
    # Cette fonction nécessite les données complètes des objets
    # Vous devrez stocker les données complètes dans detection_callback
    return []
