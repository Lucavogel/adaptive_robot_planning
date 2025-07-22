#!/usr/bin/env python3

import rospy
import tf
import moveit_commander
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float64MultiArray, String
import json

# Import conditionnel de serial
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    rospy.logwarn("Module serial non disponible, mode simulation uniquement")

class ArucoArmController:
    def __init__(self):
        if not rospy.get_node_uri():
            rospy.init_node("aruco_arm_controller")
        else:
            rospy.loginfo("Node already initialized, using existing node")

        # MoveIt
        try:
            moveit_commander.roscpp_initialize([])
            self.robot = moveit_commander.RobotCommander()
            self.group = moveit_commander.MoveGroupCommander("manipulator")
            self.moveit_available = True
        except Exception as e:
            rospy.logwarn(f"MoveIt non disponible: {e}")
            self.moveit_available = False

        self.listener = tf.TransformListener()

        # Communication série (pour LSS)
        self.use_serial = False
        if SERIAL_AVAILABLE:
            try:
                port = rospy.get_param("~serial_port", "/dev/ttyUSB0")
                baud = rospy.get_param("~baud_rate", 115200)
                self.ser = serial.Serial(port, baud, timeout=1)
                self.use_serial = True
                rospy.loginfo(f"Connexion série établie sur {port}")
            except Exception as e:
                rospy.logwarn(f"Pas de connexion série: {e}, mode simulation")
                self.use_serial = False
        else:
            rospy.logwarn("Module serial non disponible, mode simulation")

        # Publishers
        self.joint_pub = rospy.Publisher("/lss_joint_commands", Float64MultiArray, queue_size=1)
        
        # Subscribers
        self.detection_sub = rospy.Subscriber("/detected_objects", String, self.detection_callback)
        
        # Données
        self.latest_detections = {}
        self.joint_ids = rospy.get_param("~joint_ids", [1, 2, 3, 4, 5, 6])
        
        rospy.loginfo("ArUco Arm Controller initialized")

    def detection_callback(self, msg):
        """Callback pour recevoir les détections d'objets et ArUco"""
        try:
            self.latest_detections = json.loads(msg.data)
        except json.JSONDecodeError:
            rospy.logwarn("Failed to parse detection data")

    def point_to_object_with_aruco(self, object_name):
        """Pointer vers un objet en utilisant son marqueur ArUco"""
        # Attendre un peu que les données arrivent
        rospy.sleep(1.0)
        
        if not self.latest_detections or "objects" not in self.latest_detections:
            rospy.logwarn("Aucune détection disponible")
            return False
        
        # Chercher l'objet avec un marqueur ArUco
        target_object = None
        for obj in self.latest_detections["objects"]:
            if obj["name"].lower() == object_name.lower() and obj.get("aruco_marker"):
                target_object = obj
                break
        
        if not target_object:
            rospy.logwarn(f"Objet {object_name} avec marqueur ArUco non trouvé")
            # Simulation du mouvement
            rospy.loginfo(f"[SIMULATION] Pointerais vers {object_name}")
            return True
        
        # Utiliser la transformation TF du marqueur ArUco
        marker_id = target_object["aruco_marker"]["id"]
        return self.point_to_aruco_marker(marker_id)

    def point_to_aruco_marker(self, marker_id):
        """Pointer vers un marqueur ArUco spécifique"""
        try:
            # Obtenir la transformation du marqueur
            marker_frame = f"aruco_marker_{marker_id}"
            (trans, rot) = self.listener.lookupTransform("base_link", marker_frame, rospy.Time(0))
            
            rospy.loginfo(f"Marqueur ArUco {marker_id} détecté à position: {trans}")
            
            if not self.moveit_available:
                rospy.loginfo(f"[SIMULATION] Pointerais vers marqueur ArUco {marker_id} à {trans}")
                return True
            
            # Créer la pose cible
            pose = PoseStamped()
            pose.header.frame_id = "base_link"
            pose.pose.position.x = trans[0]
            pose.pose.position.y = trans[1]
            pose.pose.position.z = trans[2] + 0.1  # Pointer légèrement au-dessus
            pose.pose.orientation.x = rot[0]
            pose.pose.orientation.y = rot[1]
            pose.pose.orientation.z = rot[2]
            pose.pose.orientation.w = rot[3]

            # Augmenter le temps de planning
            self.group.set_planning_time(15)  # Au lieu de 10
            self.group.set_num_planning_attempts(10)  # Au lieu de 5
            
            # Position cible plus conservative
            pose.pose.position.z = trans[2] + 0.2  # Plus haut

            # Planifier et exécuter le mouvement
            self.group.set_pose_target(pose)

            # NOUVELLE VERSION (corrigée pour tuple de 4)
            try:
                plan_result = self.group.plan()
                rospy.loginfo(f"Debug: plan_result type = {type(plan_result)}, length = {len(plan_result) if isinstance(plan_result, tuple) else 'N/A'}")
                
                # ROS Noetic retourne (success, plan, planning_time, error_code)
                if isinstance(plan_result, tuple) and len(plan_result) >= 2:
                    success = plan_result[0]        # success (bool)
                    plan = plan_result[1]           # plan (RobotTrajectory)
                    planning_time = plan_result[2] if len(plan_result) > 2 else 0.0
                    error_code = plan_result[3] if len(plan_result) > 3 else None
                    
                    rospy.loginfo(f"✅ Plan reçu - Success: {success}, Planning time: {planning_time}s")
                    
                else:
                    rospy.logerr("Format de retour inattendu de group.plan()")
                    return False
                
                # Vérifier la validité du plan
                if success and plan and hasattr(plan, 'joint_trajectory') and plan.joint_trajectory.points:
                    rospy.loginfo(f"✅ Plan valide avec {len(plan.joint_trajectory.points)} points")
                    
                    # Exécuter le mouvement
                    rospy.loginfo("🚀 Début d'exécution du mouvement...")
                    execution_result = self.group.execute(plan, wait=True)
                    rospy.loginfo(f"✅ Exécution terminée - Résultat: {execution_result}")
                    
                    # Récupérer les angles des joints finaux
                    joint_angles = plan.joint_trajectory.points[-1].positions
                    rospy.loginfo(f"📊 Angles finaux: {[round(angle, 3) for angle in joint_angles]}")
                    
                    # Publier les commandes d'articulation
                    from std_msgs.msg import Float64MultiArray
                    msg = Float64MultiArray(data=list(joint_angles))
                    self.joint_pub.publish(msg)
                    
                    # Envoyer les commandes série si disponible
                    if self.use_serial:
                        self.send_serial_commands(joint_angles)
                    
                    rospy.loginfo("✅ Mouvement terminé avec succès !")
                    return True
                    
                else:
                    rospy.logwarn(f"❌ Plan invalide - Success: {success}")
                    if plan and hasattr(plan, 'joint_trajectory'):
                        rospy.logwarn(f"Points dans trajectory: {len(plan.joint_trajectory.points)}")
                    else:
                        rospy.logwarn("Plan n'a pas de joint_trajectory")
                    return False

            except Exception as e:
                rospy.logerr(f"❌ Erreur lors de la planification: {e}")
                import traceback
                rospy.logerr(traceback.format_exc())
                return False
                
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException) as e:
            rospy.logwarn(f"Impossible de trouver la transformation pour le marqueur {marker_id}: {e}")
            # Simulation du mouvement
            rospy.loginfo(f"[SIMULATION] Pointerais vers marqueur ArUco {marker_id}")
            return True

    def send_serial_commands(self, joint_angles):
        """Envoyer les commandes aux servomoteurs LSS"""
        if not self.use_serial:
            return
            
        for i, angle in enumerate(joint_angles):
            lss_angle = int(angle * 180.0 / 3.14159)  # rad → deg
            cmd = f"#{self.joint_ids[i]}D{lss_angle}\r\n"
            rospy.loginfo(f"Sending: {cmd.strip()}")
            self.ser.write(cmd.encode())

    def get_available_aruco_objects(self):
        """Obtenir la liste des objets avec marqueurs ArUco disponibles"""
        if not self.latest_detections or "objects" not in self.latest_detections:
            return []
        
        aruco_objects = []
        for obj in self.latest_detections["objects"]:
            if obj.get("aruco_marker"):
                aruco_objects.append({
                    "name": obj["name"],
                    "aruco_id": obj["aruco_marker"]["id"],
                    "position": obj["aruco_marker"]["position"]
                })
        
        return aruco_objects

if __name__ == "__main__":
    controller = ArucoArmController()
    rospy.spin()