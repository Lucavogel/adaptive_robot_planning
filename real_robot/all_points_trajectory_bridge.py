#!/usr/bin/env python3
"""
Bridge ROS2 qui capture TOUTE la trajectoire MoveIt de début à fin.
Collecte tous les waypoints et les sauvegarde quand la trajectoire est complète.
"""

import rclpy
from rclpy.node import Node
from moveit_msgs.msg import DisplayTrajectory
import json
import time
import os

class AllPointsTrajectoryBridge(Node):
    """
    Bridge qui capture TOUTE la trajectoire MoveIt point par point.
    """
    
    def __init__(self):
        super().__init__('all_points_trajectory_bridge')
        
        # Output file for all trajectory points
        self.output_file = '/tmp/moveit_all_points_trajectory.json'
        
        # Trajectory collection
        self.current_trajectory = []
        self.trajectory_complete = False
        self.last_trajectory_time = 0
        
        # Subscribe to MoveIt trajectory display
        self.trajectory_subscription = self.create_subscription(
            DisplayTrajectory,
            '/display_planned_path',
            self.trajectory_callback,
            10
        )
        
        print("[AllPointsBridge] 🎯 Bridge démarré - capture TOUTE la trajectoire MoveIt")
        print(f"[AllPointsBridge] Fichier de sortie: {self.output_file}")
        print("[AllPointsBridge] Waiting for MoveIt trajectories...")
        
    def trajectory_callback(self, msg):
        """
        Callback quand une nouvelle trajectoire MoveIt est reçue.
        Capture TOUS les waypoints de début à fin.
        """
        try:
            if not msg.trajectory or len(msg.trajectory) == 0:
                return
                
            # Get the trajectory (usually the first one)
            trajectory = msg.trajectory[0]
            
            if not trajectory.joint_trajectory.points:
                return
                
            current_time = time.time()
            
            # Nouvelle trajectoire si plus de 2 secondes depuis la dernière
            if current_time - self.last_trajectory_time > 2.0:
                print(f"\n[AllPointsBridge] 🆕 NOUVELLE TRAJECTOIRE DÉTECTÉE!")
                print(f"[AllPointsBridge] Joints: {trajectory.joint_trajectory.joint_names}")
                print(f"[AllPointsBridge] Nombre de waypoints: {len(trajectory.joint_trajectory.points)}")
                
                # Reset pour nouvelle trajectoire
                self.current_trajectory = []
                self.trajectory_complete = False
                
                # Collecter TOUS les waypoints
                waypoints = []
                for i, point in enumerate(trajectory.joint_trajectory.points):
                    waypoint = {
                        'positions': list(point.positions),
                        'time_from_start': point.time_from_start.sec + point.time_from_start.nanosec * 1e-9,
                        'waypoint_index': i
                    }
                    waypoints.append(waypoint)
                    
                    if i == 0:
                        print(f"[AllPointsBridge] 🏁 START: {[f'{pos:.1f}°' for pos in point.positions]}")
                    elif i == len(trajectory.joint_trajectory.points) - 1:
                        print(f"[AllPointsBridge] 🏁 END: {[f'{pos:.1f}°' for pos in point.positions]}")
                    elif i % 5 == 0:  # Show every 5th waypoint (plus de détails)
                        print(f"[AllPointsBridge] 📍 Point {i}: {[f'{pos:.1f}°' for pos in point.positions]}")
                        
                # Calculer les mouvements maximaux pour vérifier
                if len(waypoints) > 1:
                    start_pos = waypoints[0]['positions']
                    end_pos = waypoints[-1]['positions']
                    total_movement = [abs(end_pos[i] - start_pos[i]) for i in range(len(start_pos))]
                    max_total_movement = max(total_movement)
                    print(f"[AllPointsBridge] 📏 Mouvement total: {[f'{mov:.1f}°' for mov in total_movement]} (max: {max_total_movement:.1f}°)")
                    
                    if max_total_movement < 10.0:
                        print(f"[AllPointsBridge] ⚠️  ATTENTION: Mouvement très petit ({max_total_movement:.1f}°)!")
                        print(f"[AllPointsBridge] 💡 Conseil: Planifiez une trajectoire plus longue dans MoveIt")
                
                # Sauvegarder la trajectoire complète
                trajectory_data = {
                    'timestamp': current_time,
                    'joint_names': list(trajectory.joint_trajectory.joint_names),
                    'trajectory_waypoints': waypoints,
                    'total_waypoints': len(waypoints),
                    'total_duration': waypoints[-1]['time_from_start'] if waypoints else 0,
                    'bridge_ready': True,
                    'trajectory_complete': True
                }
                
                # Écrire dans le fichier
                with open(self.output_file, 'w') as f:
                    json.dump(trajectory_data, f, indent=2)
                
                print(f"[AllPointsBridge] ✅ TRAJECTOIRE COMPLÈTE SAUVEGARDÉE!")
                print(f"[AllPointsBridge] Total: {len(waypoints)} waypoints sur {waypoints[-1]['time_from_start']:.1f}s")
                print(f"[AllPointsBridge] Fichier: {self.output_file}")
                print("=" * 60)
                
                self.last_trajectory_time = current_time
                
        except Exception as e:
            print(f"[AllPointsBridge] ❌ Erreur: {e}")

def main(args=None):
    rclpy.init(args=args)
    
    # Clear old data file
    output_file = '/tmp/moveit_all_points_trajectory.json'
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"[AllPointsBridge] 🗑️ Ancien fichier supprimé")
    
    bridge = AllPointsTrajectoryBridge()
    
    try:
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        print("\n[AllPointsBridge] CTRL-C détecté, arrêt...")
    finally:
        bridge.destroy_node()
        rclpy.shutdown()
        print("[AllPointsBridge] Bridge arrêté.")

if __name__ == '__main__':
    main()
