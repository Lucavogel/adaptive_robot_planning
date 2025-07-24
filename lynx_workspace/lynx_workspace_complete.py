#!/usr/bin/env python3
"""
Analyseur complet d'espace de travail pour le robot Lynx SES900
Version sans dépendances ROS - Calcul analytique pur
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import json
import xml.etree.ElementTree as ET
import os
import sys

class LynxWorkspaceAnalyzer:
    def __init__(self, urdf_path=None):
        """Analyseur d'espace de travail pour le robot Lynx SES900"""
        print("=== ANALYSEUR D'ESPACE DE TRAVAIL LYNX SES900 ===")
        
        # Charger et analyser l'URDF
        self.urdf_path = urdf_path or "real_robot/robot_models/URDF_description/urdf/lynx_ses900_optimized.urdf"
        self.robot_info = self.parse_urdf()
        self.display_robot_info()
    
    def parse_urdf(self):
        """Analyser le fichier URDF pour extraire les informations du robot"""
        print(f"\n=== ANALYSE URDF ===")
        print(f"Fichier: {self.urdf_path}")
        
        try:
            tree = ET.parse(self.urdf_path)
            root = tree.getroot()
            
            robot_info = {
                'name': root.get('name', 'lynx_ses900'),
                'links': [],
                'joints': [],
                'joint_limits': {},
                'dh_parameters': []
            }
            
            # Analyser les liens
            for link in root.findall('link'):
                link_name = link.get('name')
                robot_info['links'].append(link_name)
                
                # Analyser les propriétés inertiales
                inertial = link.find('inertial')
                if inertial is not None:
                    mass_elem = inertial.find('mass')
                    mass = float(mass_elem.get('value')) if mass_elem is not None else 0.0
                    print(f"  Lien {link_name}: masse = {mass} kg")
            
            # Analyser les joints
            for joint in root.findall('joint'):
                joint_name = joint.get('name')
                joint_type = joint.get('type')
                
                if joint_type == 'revolute':
                    robot_info['joints'].append(joint_name)
                    
                    # Limites du joint
                    limit = joint.find('limit')
                    if limit is not None:
                        lower = float(limit.get('lower', '-3.1416'))
                        upper = float(limit.get('upper', '3.1416'))
                        effort = float(limit.get('effort', '50'))
                        velocity = float(limit.get('velocity', '1.5'))
                        
                        robot_info['joint_limits'][joint_name] = {
                            'lower': lower,
                            'upper': upper,
                            'effort': effort,
                            'velocity': velocity
                        }
                    
                    # Transformation
                    origin = joint.find('origin')
                    if origin is not None:
                        xyz = origin.get('xyz', '0 0 0').split()
                        rpy = origin.get('rpy', '0 0 0').split()
                        xyz = [float(x) for x in xyz]
                        rpy = [float(r) for r in rpy]
                        
                        axis = joint.find('axis')
                        axis_xyz = [0, 0, 1]  # Défaut
                        if axis is not None:
                            axis_xyz = [float(x) for x in axis.get('xyz', '0 0 1').split()]
                        
                        robot_info['dh_parameters'].append({
                            'joint': joint_name,
                            'translation': xyz,
                            'rotation': rpy,
                            'axis': axis_xyz
                        })
            
            print(f"✅ URDF analysé: {len(robot_info['links'])} liens, {len(robot_info['joints'])} joints")
            return robot_info
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse URDF: {e}")
            return self.get_default_lynx_info()
    
    def get_default_lynx_info(self):
        """Informations par défaut du Lynx SES900"""
        return {
            'name': 'lynx_ses900',
            'links': ['base_link', 'shoulder_link', 'upper_arm_link', 'forearm_link', 'wrist_link', 'hand_link', 'tool_link'],
            'joints': ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6'],
            'joint_limits': {
                'joint_1': {'lower': -3.1416, 'upper': 3.1416},
                'joint_2': {'lower': -3.1416, 'upper': 3.1416},
                'joint_3': {'lower': -3.1416, 'upper': 3.1416},
                'joint_4': {'lower': -3.1416, 'upper': 3.1416},
                'joint_5': {'lower': -3.1416, 'upper': 3.1416},
                'joint_6': {'lower': -3.1416, 'upper': 3.1416}
            },
            'dh_parameters': [
                {'joint': 'joint_1', 'translation': [0, 0, 0], 'rotation': [0, 0, 0], 'axis': [0, 0, -1]},
                {'joint': 'joint_2', 'translation': [-0.04, 0, 0.1], 'rotation': [0, 0, 0], 'axis': [1, 0, 0]},
                {'joint': 'joint_3', 'translation': [-0.045, 0, 0.415], 'rotation': [0, 0, 3.1416], 'axis': [1, 0, 0]},
                {'joint': 'joint_4', 'translation': [-0.05, 0, 0.05], 'rotation': [0, 0, 3.1416], 'axis': [0, 0, -1]},
                {'joint': 'joint_5', 'translation': [-0.06, 0, 0.335], 'rotation': [0, 0, 0], 'axis': [1, 0, 0]},
                {'joint': 'joint_6', 'translation': [-0.05, 0, -0.07], 'rotation': [0, 0, 0], 'axis': [0, 0, 1]}
            ]
        }
    
    def display_robot_info(self):
        """Afficher les informations du robot"""
        print(f"\n=== INFORMATIONS ROBOT ===")
        print(f"Nom: {self.robot_info['name']}")
        print(f"Nombre de joints: {len(self.robot_info['joints'])}")
        print(f"Nombre de liens: {len(self.robot_info['links'])}")
        
        print(f"\n=== LIMITES DES JOINTS ===")
        for joint, limits in self.robot_info['joint_limits'].items():
            lower_deg = np.degrees(limits['lower'])
            upper_deg = np.degrees(limits['upper'])
            print(f"{joint}: [{limits['lower']:.2f}, {limits['upper']:.2f}] rad = [{lower_deg:.1f}°, {upper_deg:.1f}°]")
        
        print(f"\n=== PARAMÈTRES DH (Denavit-Hartenberg) ===")
        for i, dh in enumerate(self.robot_info['dh_parameters']):
            trans = dh['translation']
            rot = dh['rotation']
            print(f"Joint {i+1} ({dh['joint']}):")
            print(f"  Translation: [{trans[0]:.3f}, {trans[1]:.3f}, {trans[2]:.3f}] m")
            print(f"  Rotation: [{np.degrees(rot[0]):.1f}°, {np.degrees(rot[1]):.1f}°, {np.degrees(rot[2]):.1f}°]")
            print(f"  Axe: {dh['axis']}")
    
    def rotation_matrix_x(self, angle):
        """Matrice de rotation autour de l'axe X"""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([[1, 0, 0],
                        [0, c, -s],
                        [0, s, c]])
    
    def rotation_matrix_y(self, angle):
        """Matrice de rotation autour de l'axe Y"""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([[c, 0, s],
                        [0, 1, 0],
                        [-s, 0, c]])
    
    def rotation_matrix_z(self, angle):
        """Matrice de rotation autour de l'axe Z"""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([[c, -s, 0],
                        [s, c, 0],
                        [0, 0, 1]])
    
    def calculate_forward_kinematics(self, joint_angles):
        """Calculer la cinématique directe"""
        if len(joint_angles) != 6:
            raise ValueError("Il faut exactement 6 angles de joints")
        
        # Matrice de transformation finale
        T_final = np.eye(4)
        
        for i, (angle, dh) in enumerate(zip(joint_angles, self.robot_info['dh_parameters'])):
            # Transformation du joint
            trans = dh['translation']
            rot = dh['rotation']
            axis = dh['axis']
            
            # Matrice de transformation locale
            T_local = np.eye(4)
            
            # Translation fixe
            T_local[0:3, 3] = trans
            
            # Rotation fixe
            R_fixed = np.eye(3)
            if rot[0] != 0:  # Rotation autour de X
                R_fixed = self.rotation_matrix_x(rot[0]) @ R_fixed
            if rot[1] != 0:  # Rotation autour de Y
                R_fixed = self.rotation_matrix_y(rot[1]) @ R_fixed
            if rot[2] != 0:  # Rotation autour de Z
                R_fixed = self.rotation_matrix_z(rot[2]) @ R_fixed
            
            T_local[0:3, 0:3] = R_fixed
            
            # Rotation du joint
            if abs(axis[0]) > 0.5:  # Rotation autour de X
                R_joint = self.rotation_matrix_x(angle * np.sign(axis[0]))
            elif abs(axis[1]) > 0.5:  # Rotation autour de Y
                R_joint = self.rotation_matrix_y(angle * np.sign(axis[1]))
            else:  # Rotation autour de Z
                R_joint = self.rotation_matrix_z(angle * np.sign(axis[2]))
            
            T_joint = np.eye(4)
            T_joint[0:3, 0:3] = R_joint
            
            # Combiner les transformations
            T_final = T_final @ T_local @ T_joint
        
        # Position de l'effecteur terminal
        position = T_final[0:3, 3]
        orientation = T_final[0:3, 0:3]
        
        return position, orientation, T_final
    
    def sample_workspace_analytical(self, num_samples=10000):
        """Échantillonnage analytique de l'espace de travail"""
        print(f"\n=== ÉCHANTILLONNAGE ANALYTIQUE ({num_samples} échantillons) ===")
        
        reachable_points = []
        
        for i in range(num_samples):
            if i % 1000 == 0:
                progress = (i / num_samples) * 100
                print(f"Progression: {progress:.1f}% ({i}/{num_samples})")
            
            # Générer des angles de joints aléatoires dans les limites
            joint_angles = []
            for joint_name in self.robot_info['joints']:
                limits = self.robot_info['joint_limits'][joint_name]
                angle = np.random.uniform(limits['lower'], limits['upper'])
                joint_angles.append(angle)
            
            try:
                position, _, _ = self.calculate_forward_kinematics(joint_angles)
                reachable_points.append(position)
            except Exception as e:
                continue
        
        print(f"✅ {len(reachable_points)} points calculés")
        return np.array(reachable_points)
    
    def analyze_workspace_envelope(self, points):
        """Analyser l'enveloppe de l'espace de travail"""
        print(f"\n=== ANALYSE DE L'ENVELOPPE ===")
        
        if len(points) == 0:
            print("❌ Aucun point à analyser")
            return {}
        
        # Statistiques de base
        x, y, z = points[:, 0], points[:, 1], points[:, 2]
        
        analysis = {
            'num_points': len(points),
            'bounds': {
                'x': {'min': float(np.min(x)), 'max': float(np.max(x)), 'range': float(np.max(x) - np.min(x))},
                'y': {'min': float(np.min(y)), 'max': float(np.max(y)), 'range': float(np.max(y) - np.min(y))},
                'z': {'min': float(np.min(z)), 'max': float(np.max(z)), 'range': float(np.max(z) - np.min(z))}
            },
            'reach': {
                'max_distance': float(np.max(np.sqrt(x**2 + y**2 + z**2))),
                'min_distance': float(np.min(np.sqrt(x**2 + y**2 + z**2))),
                'max_xy_distance': float(np.max(np.sqrt(x**2 + y**2)))
            },
            'volume': {
                'bounding_box': float((np.max(x) - np.min(x)) * (np.max(y) - np.min(y)) * (np.max(z) - np.min(z))),
                'workspace_efficiency': 0.0
            }
        }
        
        # Affichage des résultats
        print(f"Nombre de points: {analysis['num_points']}")
        print(f"Limites X: [{analysis['bounds']['x']['min']:.3f}, {analysis['bounds']['x']['max']:.3f}] m (range: {analysis['bounds']['x']['range']:.3f} m)")
        print(f"Limites Y: [{analysis['bounds']['y']['min']:.3f}, {analysis['bounds']['y']['max']:.3f}] m (range: {analysis['bounds']['y']['range']:.3f} m)")
        print(f"Limites Z: [{analysis['bounds']['z']['min']:.3f}, {analysis['bounds']['z']['max']:.3f}] m (range: {analysis['bounds']['z']['range']:.3f} m)")
        print(f"Portée maximale: {analysis['reach']['max_distance']:.3f} m")
        print(f"Portée minimale: {analysis['reach']['min_distance']:.3f} m")
        print(f"Portée XY maximale: {analysis['reach']['max_xy_distance']:.3f} m")
        print(f"Volume boîte englobante: {analysis['volume']['bounding_box']:.3f} m³")
        
        return analysis
    
    def visualize_workspace(self, points, save_path=None):
        """Visualiser l'espace de travail"""
        print(f"\n=== VISUALISATION ===")
        
        if len(points) == 0:
            print("❌ Aucun point à visualiser")
            return
        
        # Créer la figure avec sous-graphiques
        fig = plt.figure(figsize=(18, 6))
        
        # Vue 3D
        ax1 = fig.add_subplot(131, projection='3d')
        scatter = ax1.scatter(points[:, 0], points[:, 1], points[:, 2], 
                             c=points[:, 2], alpha=0.3, s=0.5, cmap='viridis')
        ax1.set_xlabel('X (m)')
        ax1.set_ylabel('Y (m)')
        ax1.set_zlabel('Z (m)')
        ax1.set_title('Espace de travail 3D - Lynx SES900')
        plt.colorbar(scatter, ax=ax1, label='Hauteur Z (m)')
        
        # Vue XY (de dessus)
        ax2 = fig.add_subplot(132)
        ax2.scatter(points[:, 0], points[:, 1], alpha=0.3, s=0.5, c=points[:, 2], cmap='viridis')
        ax2.set_xlabel('X (m)')
        ax2.set_ylabel('Y (m)')
        ax2.set_title('Vue de dessus (XY)')
        ax2.grid(True, alpha=0.3)
        ax2.axis('equal')
        
        # Vue XZ (de côté)
        ax3 = fig.add_subplot(133)
        ax3.scatter(points[:, 0], points[:, 2], alpha=0.3, s=0.5, c=points[:, 1], cmap='plasma')
        ax3.set_xlabel('X (m)')
        ax3.set_ylabel('Z (m)')
        ax3.set_title('Vue de côté (XZ)')
        ax3.grid(True, alpha=0.3)
        ax3.axis('equal')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Graphique sauvegardé: {save_path}")
        
        # Sauvegarder aussi une version avec différentes vues
        fig2, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Histogrammes de distribution
        axes[0,0].hist(points[:, 0], bins=50, alpha=0.7, color='red', label='X')
        axes[0,0].hist(points[:, 1], bins=50, alpha=0.7, color='green', label='Y')
        axes[0,0].hist(points[:, 2], bins=50, alpha=0.7, color='blue', label='Z')
        axes[0,0].set_title('Distribution des positions')
        axes[0,0].set_xlabel('Position (m)')
        axes[0,0].set_ylabel('Fréquence')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # Distance depuis l'origine
        distances = np.sqrt(points[:, 0]**2 + points[:, 1]**2 + points[:, 2]**2)
        axes[0,1].hist(distances, bins=50, alpha=0.7, color='purple')
        axes[0,1].set_title('Distribution des distances depuis l\'origine')
        axes[0,1].set_xlabel('Distance (m)')
        axes[0,1].set_ylabel('Fréquence')
        axes[0,1].grid(True, alpha=0.3)
        
        # Vue polaire XY
        angles = np.arctan2(points[:, 1], points[:, 0])
        distances_xy = np.sqrt(points[:, 0]**2 + points[:, 1]**2)
        axes[1,0].scatter(angles, distances_xy, alpha=0.3, s=0.5)
        axes[1,0].set_title('Vue polaire (XY)')
        axes[1,0].set_xlabel('Angle (rad)')
        axes[1,0].set_ylabel('Distance XY (m)')
        axes[1,0].grid(True, alpha=0.3)
        
        # Analyse par hauteur
        unique_z = np.unique(np.round(points[:, 2], 2))
        max_radius_per_z = []
        for z_val in unique_z:
            mask = np.abs(points[:, 2] - z_val) < 0.01
            if np.sum(mask) > 0:
                max_r = np.max(np.sqrt(points[mask, 0]**2 + points[mask, 1]**2))
                max_radius_per_z.append(max_r)
            else:
                max_radius_per_z.append(0)
        
        axes[1,1].plot(unique_z, max_radius_per_z, 'b-o', markersize=2)
        axes[1,1].set_title('Portée maximale par hauteur')
        axes[1,1].set_xlabel('Hauteur Z (m)')
        axes[1,1].set_ylabel('Portée maximale XY (m)')
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            analysis_path = save_path.replace('.png', '_analysis.png')
            plt.savefig(analysis_path, dpi=300, bbox_inches='tight')
            print(f"✅ Graphique d'analyse sauvegardé: {analysis_path}")
        
        plt.show()
    
    def save_analysis(self, points, analysis, filename="lynx_workspace_data.json"):
        """Sauvegarder l'analyse"""
        print(f"\n=== SAUVEGARDE ===")
        
        data = {
            'robot_model': self.robot_info['name'],
            'analysis_type': 'analytical_forward_kinematics',
            'timestamp': 'analytical_computation',
            'robot_info': self.robot_info,
            'analysis': analysis,
            'points': points.tolist() if len(points) > 0 else []
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Données sauvegardées: {filename}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
    
    def run_complete_analysis(self, num_samples=20000):
        """Exécuter une analyse complète"""
        print(f"\n{'='*60}")
        print(f"ANALYSE COMPLÈTE DE L'ESPACE DE TRAVAIL")
        print(f"Robot: {self.robot_info['name']}")
        print(f"Échantillons: {num_samples}")
        print(f"{'='*60}")
        
        # 1. Échantillonnage
        points = self.sample_workspace_analytical(num_samples)
        
        # 2. Analyse
        analysis = self.analyze_workspace_envelope(points)
        
        # 3. Visualisation
        self.visualize_workspace(points, "lynx_workspace_complete.png")
        
        # 4. Sauvegarde
        self.save_analysis(points, analysis, "lynx_workspace_complete.json")
        
        return points, analysis

def main():
    if len(sys.argv) > 1:
        urdf_path = sys.argv[1]
    else:
        urdf_path = None
    
    analyzer = LynxWorkspaceAnalyzer(urdf_path)
    points, analysis = analyzer.run_complete_analysis(num_samples=20000)
    
    print(f"\n🎉 Analyse terminée!")
    print(f"📊 {len(points)} points analysés")
    print(f"📁 Données sauvegardées dans lynx_workspace_complete.json")
    print(f"📈 Graphiques sauvegardés dans lynx_workspace_complete.png")

if __name__ == "__main__":
    main()
