#!/usr/bin/env python3

import rospy
import moveit_commander
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
from geometry_msgs.msg import PoseStamped
import tf.transformations as tf_trans

class WorkspaceAnalyzer:
    def __init__(self):
        rospy.init_node("workspace_analyzer")
        
        # Initialiser MoveIt
        moveit_commander.roscpp_initialize([])
        self.robot = moveit_commander.RobotCommander()
        self.group = moveit_commander.MoveGroupCommander("manipulator")
        
        print("=== ANALYSEUR D'ESPACE DE TRAVAIL UR5 ===")
        
        # Informations du robot (avec gestion d'erreur)
        try:
            robot_name = self.robot.get_robot_model().getName()
            print(f"Robot: {robot_name}")
        except AttributeError:
            print("Robot: UR5 (détection automatique)")
    
        print(f"Groupe: {self.group.get_name()}")
        print(f"Frame de référence: {self.group.get_planning_frame()}")
        print(f"End-effector: {self.group.get_end_effector_link()}")
        
        # Liste des joints
        joint_names = self.group.get_active_joints()
        print(f"Joints actifs: {len(joint_names)}")
        for i, joint in enumerate(joint_names):
            print(f"  {i+1}. {joint}")
        
    def get_joint_limits(self):
        """Récupérer les limites des joints"""
        joint_names = self.group.get_active_joints()
        print(f"\n=== LIMITES DES JOINTS ===")
        
        # Limites typiques UR5 (en radians)
        joint_limits = {
            'shoulder_pan_joint': (-np.pi, np.pi),
            'shoulder_lift_joint': (-np.pi, np.pi), 
            'elbow_joint': (-np.pi, np.pi),
            'wrist_1_joint': (-np.pi, np.pi),
            'wrist_2_joint': (-np.pi, np.pi),
            'wrist_3_joint': (-np.pi, np.pi)
        }
        
        for joint in joint_names:
            if joint in joint_limits:
                min_val, max_val = joint_limits[joint]
                print(f"{joint}: [{min_val:.2f}, {max_val:.2f}] rad = [{np.degrees(min_val):.1f}°, {np.degrees(max_val):.1f}°]")
        
        return joint_limits
    
    def sample_workspace_grid(self, resolution=0.1):
        """Échantillonner l'espace de travail sur une grille 3D"""
        print(f"\n=== ÉCHANTILLONNAGE ESPACE DE TRAVAIL (résolution: {resolution}m) ===")
        
        # Définir les limites de la grille de recherche
        x_range = np.arange(-1.0, 1.0, resolution)
        y_range = np.arange(-1.0, 1.0, resolution) 
        z_range = np.arange(0.0, 1.5, resolution)
        
        reachable_points = []
        total_points = len(x_range) * len(y_range) * len(z_range)
        current_point = 0
        
        print(f"Test de {total_points} points...")
        
        for x in x_range:
            for y in y_range:
                for z in z_range:
                    current_point += 1
                    if current_point % 500 == 0:
                        progress = (current_point / total_points) * 100
                        print(f"Progression: {progress:.1f}% ({current_point}/{total_points})")
                    
                    # Tester si cette position est atteignable
                    if self.test_position_reachable(x, y, z):
                        reachable_points.append([x, y, z])
        
        print(f"✅ {len(reachable_points)} points atteignables trouvés sur {total_points}")
        return np.array(reachable_points)
    
    def test_position_reachable(self, x, y, z, timeout=1.0):  # ⬅️ Changer de 0.1 à 1.0
        """Tester si une position (x,y,z) est atteignable"""
        try:
            # Créer une pose cible
            pose = PoseStamped()
            pose.header.frame_id = self.group.get_planning_frame()
            pose.pose.position.x = x
            pose.pose.position.y = y
            pose.pose.position.z = z
            
            # Orientation par défaut (end-effector vers le bas)
            pose.pose.orientation.x = 0.0
            pose.pose.orientation.y = 0.707
            pose.pose.orientation.z = 0.0
            pose.pose.orientation.w = 0.707
            
            # Configuration pour test rapide - AMÉLIORÉE
            self.group.set_planning_time(timeout)  # Plus de temps
            self.group.set_num_planning_attempts(3)  # Plus de tentatives
            self.group.set_goal_position_tolerance(0.1)  # Plus de tolérance
            self.group.set_pose_target(pose)
            
            # Tester la planification
            plan_result = self.group.plan()
            
            if isinstance(plan_result, tuple):
                success = plan_result[0]
                plan = plan_result[1] if len(plan_result) > 1 else None
            else:
                plan = plan_result
                success = plan is not None and hasattr(plan, 'joint_trajectory')
                if success:
                    success = len(plan.joint_trajectory.points) > 0
                    
            return success
            
        except Exception:
            return False
    
    def test_position_reachable_geometric(self, x, y, z):
        """Test géométrique rapide de l'atteignabilité"""
        distance_3d = np.sqrt(x**2 + y**2 + z**2)
        distance_xy = np.sqrt(x**2 + y**2)
        
        # Limites UR5
        if distance_3d > 0.85: return False  # Portée max
        if distance_xy < 0.15: return False  # Trop proche
        if z < 0.05 or z > 1.2: return False  # Hauteur
        if distance_xy < 0.2 and z < 0.2: return False  # Collision base
        
        return True
    
    def sample_workspace_random(self, num_samples=2000):
        """Échantillonnage aléatoire plus rapide"""
        print(f"\n=== ÉCHANTILLONNAGE ALÉATOIRE ({num_samples} échantillons) ===")
        
        reachable_points = []
        
        for i in range(num_samples):
            if i % 200 == 0:
                progress = (i / num_samples) * 100
                print(f"Progression: {progress:.1f}% ({i}/{num_samples})")
            
            # Générer une position aléatoire dans une sphère
            radius = np.random.uniform(0.2, 1.0)
            theta = np.random.uniform(0, 2*np.pi)
            phi = np.random.uniform(0, np.pi)
            
            x = radius * np.sin(phi) * np.cos(theta)
            y = radius * np.sin(phi) * np.sin(theta) 
            z = radius * np.cos(phi) + 0.5  # Décaler vers le haut
            
            if self.test_position_reachable(x, y, z, timeout=0.5):  # ⬅️ Changer de 0.05 à 0.5
                reachable_points.append([x, y, z])
        
        print(f"✅ {len(reachable_points)} points atteignables trouvés sur {num_samples}")
        return np.array(reachable_points)
    
    def analyze_current_position(self):
        """Analyser la position actuelle du robot"""
        print(f"\n=== POSITION ACTUELLE ===")
        
        # Position cartésienne
        current_pose = self.group.get_current_pose().pose
        print(f"Position: x={current_pose.position.x:.3f}, y={current_pose.position.y:.3f}, z={current_pose.position.z:.3f}")
        print(f"Orientation: x={current_pose.orientation.x:.3f}, y={current_pose.orientation.y:.3f}, z={current_pose.orientation.z:.3f}, w={current_pose.orientation.w:.3f}")
        
        # Joints
        current_joints = self.group.get_current_joint_values()
        joint_names = self.group.get_active_joints()
        print("Joints actuels:")
        for name, angle in zip(joint_names, current_joints):
            print(f"  {name}: {angle:.3f} rad = {np.degrees(angle):.1f}°")
        
        # Distance du centre
        distance = np.sqrt(current_pose.position.x**2 + current_pose.position.y**2 + current_pose.position.z**2)
        print(f"Distance du centre: {distance:.3f}m")
        
        return current_pose, current_joints
    
    def save_workspace_data(self, points, filename="workspace_data.json"):
        """Sauvegarder les données d'espace de travail"""
        data = {
            "robot_model": "ur5_robot",  # ✅
            "group_name": self.group.get_name(),
            "num_points": len(points),
            "points": points.tolist(),
            "analysis_timestamp": rospy.Time.now().to_sec()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Données sauvegardées dans {filename}")
    
    def plot_workspace_3d(self, points):
        """Visualiser l'espace de travail en 3D"""
        print(f"\n=== VISUALISATION 3D ===")
        
        if len(points) == 0:
            print("❌ Aucun point à visualiser")
            return
        
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Scatter plot des points atteignables
        ax.scatter(points[:, 0], points[:, 1], points[:, 2], 
                  c=points[:, 2], cmap='viridis', alpha=0.6, s=1)
        
        # Position actuelle du robot
        current_pose, _ = self.analyze_current_position()
        ax.scatter([current_pose.position.x], [current_pose.position.y], [current_pose.position.z], 
                  c='red', s=100, marker='o', label='Position actuelle')
        
        # Origine (base du robot)
        ax.scatter([0], [0], [0], c='black', s=100, marker='s', label='Base robot')
        
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')
        ax.set_zlabel('Z (m)')
        ax.set_title(f'Espace de travail UR5 ({len(points)} points)')
        ax.legend()
        
        # Limites des axes
        max_range = np.max(np.abs(points))
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([0, max_range])
        
        plt.tight_layout()
        plt.savefig('ur5_workspace.png', dpi=300, bbox_inches='tight')
        print("📊 Graphique sauvegardé: ur5_workspace.png")
        plt.show()
    
    def calculate_workspace_metrics(self, points):
        """Calculer les métriques de l'espace de travail"""
        print(f"\n=== MÉTRIQUES ESPACE DE TRAVAIL ===")
        
        if len(points) == 0:
            print("❌ Aucun point pour calculer les métriques")
            return
        
        # Volume approximatif
        x_range = np.max(points[:, 0]) - np.min(points[:, 0])
        y_range = np.max(points[:, 1]) - np.min(points[:, 1]) 
        z_range = np.max(points[:, 2]) - np.min(points[:, 2])
        volume_approx = x_range * y_range * z_range
        
        # Portée maximale
        distances = np.sqrt(np.sum(points**2, axis=1))
        max_reach = np.max(distances)
        avg_reach = np.mean(distances)
        
        # Limites
        print(f"Limites X: [{np.min(points[:, 0]):.3f}, {np.max(points[:, 0]):.3f}] m")
        print(f"Limites Y: [{np.min(points[:, 1]):.3f}, {np.max(points[:, 1]):.3f}] m") 
        print(f"Limites Z: [{np.min(points[:, 2]):.3f}, {np.max(points[:, 2]):.3f}] m")
        print(f"Volume approximatif: {volume_approx:.3f} m³")
        print(f"Portée maximale: {max_reach:.3f} m")
        print(f"Portée moyenne: {avg_reach:.3f} m")
        print(f"Nombre de points atteignables: {len(points)}")
    
    def sample_workspace_grid_geometric(self, resolution=0.1):
        """Échantillonner l'espace de travail sur une grille 3D - Méthode géométrique"""
        print(f"\n=== ÉCHANTILLONNAGE GÉOMÉTRIQUE SUR GRILLE (résolution: {resolution}m) ===")
        
        # Définir les limites de la grille de recherche
        x_range = np.arange(-1.0, 1.0, resolution)
        y_range = np.arange(-1.0, 1.0, resolution) 
        z_range = np.arange(0.0, 1.5, resolution)
        
        reachable_points = []
        total_points = len(x_range) * len(y_range) * len(z_range)
        current_point = 0
        
        print(f"Test de {total_points} points...")
        
        for x in x_range:
            for y in y_range:
                for z in z_range:
                    current_point += 1
                    if current_point % 500 == 0:
                        progress = (current_point / total_points) * 100
                        print(f"Progression: {progress:.1f}% ({current_point}/{total_points})")
                    
                    # Tester si cette position est atteignable
                    if self.test_position_reachable_geometric(x, y, z):  # ✅
                        reachable_points.append([x, y, z])
        
        print(f"✅ {len(reachable_points)} points atteignables trouvés sur {total_points}")
        return np.array(reachable_points)
    
    def sample_workspace_random_geometric(self, num_samples=2000):
        """Échantillonnage aléatoire - Méthode géométrique"""
        print(f"\n=== ÉCHANTILLONNAGE ALÉATOIRE GÉOMÉTRIQUE ({num_samples} échantillons) ===")
        
        reachable_points = []
        
        for i in range(num_samples):
            if i % 200 == 0:
                progress = (i / num_samples) * 100
                print(f"Progression: {progress:.1f}% ({i}/{num_samples})")
            
            # Générer une position aléatoire dans une sphère
            radius = np.random.uniform(0.2, 1.0)
            theta = np.random.uniform(0, 2*np.pi)
            phi = np.random.uniform(0, np.pi)
            
            x = radius * np.sin(phi) * np.cos(theta)
            y = radius * np.sin(phi) * np.sin(theta) 
            z = radius * np.cos(phi) + 0.5  # Décaler vers le haut
            
            if self.test_position_reachable_geometric(x, y, z):  # ✅
                reachable_points.append([x, y, z])
        
        print(f"✅ {len(reachable_points)} points atteignables trouvés sur {num_samples}")
        return np.array(reachable_points)

def main():
    analyzer = WorkspaceAnalyzer()
    
    # Analyser la position actuelle
    analyzer.analyze_current_position()
    
    # Obtenir les limites des joints
    analyzer.get_joint_limits()
    
    # Choix de la méthode d'échantillonnage
    print(f"\n=== CHOIX DE LA MÉTHODE ===")
    print("1. Échantillonnage sur grille (précis mais lent)")
    print("2. Échantillonnage aléatoire (rapide)")
    print("3. Test géométrique rapide (très rapide)")
    
    choice = input("Choisissez (1, 2 ou 3): ").strip()
    
    if choice == "1":
        resolution = float(input("Résolution (ex: 0.2): "))
        points = analyzer.sample_workspace_grid_geometric(resolution)
    elif choice == "2":
        num_samples = int(input("Nombre d'échantillons (ex: 2000): "))
        points = analyzer.sample_workspace_random_geometric(num_samples)
    else:
        # Test géométrique rapide
        points = analyzer.sample_workspace_grid_geometric(0.05)
    
    if len(points) > 0:
        # Calculs des métriques
        analyzer.calculate_workspace_metrics(points)
        
        # Sauvegarde
        analyzer.save_workspace_data(points)
        
        # Visualisation
        try:
            analyzer.plot_workspace_3d(points)
        except Exception as e:
            print(f"⚠️ Erreur visualisation: {e}")
    
    print(f"\n=== ANALYSE TERMINÉE ===")

if __name__ == "__main__":
    main()