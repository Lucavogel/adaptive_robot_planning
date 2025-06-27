#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
import cv2
from ultralytics import YOLO
import json
import time

class CameraDetectionNode:
    def __init__(self):
        rospy.init_node('camera_detection_node', anonymous=True)
        
        # publisher for detected objects
        self.detection_pub = rospy.Publisher('/detected_objects', String, queue_size=10)

        try:
            self.model = YOLO("yolov8n.pt")
            rospy.loginfo("YOLO model loaded successfully")
        except Exception as e:
            rospy.logerr(f"Failed to load YOLO model: {e}")
            return
        
        self.cap = None
        self.setup_camera()
        self.detection_rate = rospy.Rate(5)  
        rospy.loginfo("Camera detection node initialized")
        
    def setup_camera(self):
        
        for device_id in [0, 1, 2, 3]:
            rospy.loginfo(f"Trying camera device {device_id}")
            cap = cv2.VideoCapture(device_id)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    rospy.loginfo(f"Camera device {device_id}")
                    self.cap = cap
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    return
                else:
                    cap.release()
            else:
                cap.release()
        
        rospy.logerr("No working camera found")
        
    def run_detection(self):
       
        if self.cap is None:
            rospy.logerr("No camera available")
            return
            
        frame_count = 0
        
        while not rospy.is_shutdown():
            ret, frame = self.cap.read()
            
            if not ret:
                rospy.logwarn("Failed to capture frame")
                continue
                
            frame_count += 1
            
            try:

                results = self.model(frame, verbose=False)
                detected_objects = []
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            class_id = int(box.cls[0])
                            class_name = self.model.names[class_id]
                            confidence = float(box.conf[0])
                            
                            if confidence > 0.5:
                                detected_objects.append({
                                    'name': class_name,
                                    'confidence': confidence
                                })
                
                # publish detection results
                detection_msg = String()
                detection_msg.data = json.dumps({
                    'timestamp': time.time(),
                    'objects': detected_objects
                })
                self.detection_pub.publish(detection_msg)
                
                # display detection info every 10 frames
                if frame_count % 10 == 0:
                    object_names = [obj['name'] for obj in detected_objects]
                    if object_names:
                        unique_objects = list(set(object_names))
                        print(f"Frame {frame_count}: Detected {len(detected_objects)} objects")
                        print(f"Objects: {', '.join(unique_objects)}")
                    else:
                        print(f"Frame {frame_count}: No objects detected")
                
                try:
                    if detected_objects:
                        annotated_frame = results[0].plot()
                        cv2.imshow('YOLO Detection', annotated_frame)
                    else:
                        cv2.imshow('YOLO Detection', frame)
                        
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                except:
                    pass 
                    
            except Exception as e:
                rospy.logwarn(f"Detection error: {e}")
                
            self.detection_rate.sleep()
                
    def cleanup(self):
        
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        node = CameraDetectionNode()
        node.run_detection()
    except rospy.ROSInterruptException:
        rospy.loginfo("Camera detection node shutting down")
    except KeyboardInterrupt:
        rospy.loginfo("Shutting down camera detection node")
    finally:
        if 'node' in locals():
            node.cleanup()