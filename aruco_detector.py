#!/usr/bin/env python3

import rospy
import cv2
import cv2.aruco as aruco
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import String
import json
import tf
from collections import deque
import os
import sys

# Supprimer les warnings FFmpeg
os.environ['OPENCV_LOG_LEVEL'] = 'FATAL'
os.environ['FFMPEG_LOG_LEVEL'] = 'FATAL'

class ArucoDetector:
    def __init__(self):
        rospy.init_node("aruco_detector", anonymous=True)
        self.bridge = CvBridge()

        # ✅ NOUVELLE SYNTAXE OpenCV 4.12.0
        rospy.loginfo("Utilisation d'OpenCV 4.12.0 - Nouvelle syntaxe ArUco")
        
        # Dictionnaire ArUco
        self.aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)
        
        # Paramètres du détecteur (nouvelle syntaxe)
        self.parameters = aruco.DetectorParameters()
        
        # Configuration des paramètres
        self.parameters.adaptiveThreshWinSizeMin = 3
        self.parameters.adaptiveThreshWinSizeMax = 23
        self.parameters.adaptiveThreshWinSizeStep = 10
        self.parameters.cornerRefinementMethod = aruco.CORNER_REFINE_SUBPIX
        self.parameters.minMarkerPerimeterRate = 0.02
        self.parameters.maxMarkerPerimeterRate = 4.0
        self.parameters.polygonalApproxAccuracyRate = 0.03
        self.parameters.minCornerDistanceRate = 0.05
        self.parameters.minDistanceToBorder = 3
        self.parameters.errorCorrectionRate = 0.6
        
        # ✅ CRÉER LE DÉTECTEUR (obligatoire en OpenCV 4.x)
        self.detector = aruco.ArucoDetector(self.aruco_dict, self.parameters)
        
        # Historique des poses pour lissage
        self.pose_history = {}
        
        # Charger les paramètres de calibration
        try:
            calib_path = "/home/soltani/catkin_ws/src/adaptive_robot_planning/calibration_data.npz"
            data = np.load(calib_path)
            self.camera_matrix = data['camera_matrix']
            self.dist_coeffs = data['dist_coeffs']
            rospy.loginfo("Paramètres de calibration chargés")
        except FileNotFoundError:
            rospy.logwarn("Fichier de calibration non trouvé, utilisation de valeurs par défaut")
            self.camera_matrix = np.array([
                [640.0, 0.0, 320.0],
                [0.0, 640.0, 240.0],
                [0.0, 0.0, 1.0]
            ])
            self.dist_coeffs = np.zeros((4, 1))
        
        # Publishers
        self.aruco_pub = rospy.Publisher("/aruco_detections", String, queue_size=10)
        self.tf_broadcaster = tf.TransformBroadcaster()
        
        self.image_sub = rospy.Subscriber("/usb_cam/image_raw", Image, self.callback)
        
        # Compteur de frames
        self.frame_count = 0
        
        rospy.loginfo("ArUco Detector initialized avec OpenCV 4.12.0")

    def callback(self, data):
        self.frame_count += 1
        frame = self.bridge.imgmsg_to_cv2(data, "bgr8")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # ✅ NOUVELLE SYNTAXE DÉTECTION OpenCV 4.12.0
        corners, ids, _ = self.detector.detectMarkers(gray)

        markers_data = []
        if ids is not None:
            print(f"✅ Marqueurs détectés: {ids.flatten()}")
            rospy.loginfo(f"ArUco détecté: {ids.flatten()}")
            
            # ✅ NOUVELLE SYNTAXE DRAWING
            aruco.drawDetectedMarkers(frame, corners, ids)
            
            for i in range(len(ids)):
                marker_info = {
                    "id": int(ids[i][0]),
                    "corners": corners[i].tolist(),
                    "dictionary": "DICT_4X4_50"
                }
                markers_data.append(marker_info)
                
                # Publier la transformation TF pour chaque marqueur
                self.tf_broadcaster.sendTransform(
                    (0.5, 0.2, 0.3),
                    (0.0, 0.0, 0.0, 1.0),
                    rospy.Time.now(),
                    f"aruco_marker_{marker_info['id']}",
                    "usb_cam"
                )
        else:
            if self.frame_count % 30 == 0:
                print(f"🔍 Frame {self.frame_count}: Aucun marqueur détecté")

        # Publier les données
        aruco_msg = String()
        aruco_msg.data = json.dumps({
            'frame_id': self.frame_count,
            'timestamp': rospy.Time.now().to_sec(),
            'markers': markers_data,
            'total_markers': len(markers_data)
        })
        self.aruco_pub.publish(aruco_msg)

        cv2.imshow("ArUco Detection OpenCV 4.12", frame)
        cv2.waitKey(1)

    def rotation_matrix_to_quaternion(self, R):
        """Convertir une matrice de rotation en quaternion"""
        trace = np.trace(R)
        if trace > 0:
            s = np.sqrt(trace + 1.0) * 2
            w = 0.25 * s
            x = (R[2, 1] - R[1, 2]) / s
            y = (R[0, 2] - R[2, 0]) / s
            z = (R[1, 0] - R[0, 1]) / s
        else:
            if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
                s = np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2
                w = (R[2, 1] - R[1, 2]) / s
                x = 0.25 * s
                y = (R[0, 1] + R[1, 0]) / s
                z = (R[0, 2] + R[2, 0]) / s
            elif R[1, 1] > R[2, 2]:
                s = np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2
                w = (R[0, 2] - R[2, 0]) / s
                x = (R[0, 1] + R[1, 0]) / s
                y = 0.25 * s
                z = (R[1, 2] + R[2, 1]) / s
            else:
                s = np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2
                w = (R[1, 0] - R[0, 1]) / s
                x = (R[0, 2] + R[2, 0]) / s
                y = (R[1, 2] + R[2, 1]) / s
                z = 0.25 * s
        return [x, y, z, w]

if __name__ == '__main__':
    try:
        ArucoDetector()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    cv2.destroyAllWindows()
