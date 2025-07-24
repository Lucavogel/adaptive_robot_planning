#!/usr/bin/env python3
# filepath: /home/soltani/catkin_ws/src/adaptive_robot_planning/capture_calibration.py

import rospy
import cv2
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class CalibrationCapture:
    def __init__(self):
        rospy.init_node("calibration_capture")
        self.bridge = CvBridge()
        self.image_sub = rospy.Subscriber("/usb_cam/image_raw", Image, self.callback)
        self.image_count = 0
        rospy.loginfo("Calibration capture started. Press SPACE to capture image, ESC to quit")

    def callback(self, data):
        try:
            frame = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except Exception as e:
            rospy.logerr(e)
            return

        cv2.imshow("Calibration Capture", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):  # Espace pour capturer
            filename = f"calib_images/calib_{self.image_count:02d}.jpg"
            cv2.imwrite(filename, frame)
            rospy.loginfo(f"Image sauvegardée: {filename}")
            self.image_count += 1
            
        elif key == 27:  # ESC pour quitter
            rospy.signal_shutdown("User quit")

if __name__ == '__main__':
    try:
        CalibrationCapture()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    cv2.destroyAllWindows()