#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import json
import time

class detectionsubscriber:
    def __init__(self):
        self.latest_objects = []
        self.last_update = 0
        self.subscriber = rospy.Subscriber('/detected_objects', String, self.detection_callback)
        rospy.loginfo("subscribed to detection topic")
    
    def detection_callback(self, msg):
        try:
            data = json.loads(msg.data)
            self.latest_objects = [obj['name'] for obj in data['objects']]
            self.last_update = time.time()
        except json.JSONDecodeError:
            rospy.logwarn("failed to parse detection data")

detection_subscriber = None

def get_environment_context():
    global detection_subscriber
    if detection_subscriber is None:
        detection_subscriber = detectionsubscriber()
        rospy.sleep(0.5)
    
    if detection_subscriber.latest_objects:
        objects_str = ", ".join(set(detection_subscriber.latest_objects))
        return f"#####the robot sees: {objects_str}."
    else:
        return "#####the robot sees: nothing."

def get_latest_objects():
    global detection_subscriber
    if detection_subscriber is None:
        detection_subscriber = detectionsubscriber()

    return detection_subscriber.latest_objects.copy()
