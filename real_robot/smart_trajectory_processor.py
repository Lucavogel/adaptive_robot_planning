#!/usr/bin/env python3
"""
Bridge intelligent qui PRÉ-CALCULE toute la trajectoire avec vitesses adaptatives
et stocke tout dans un JSON optimisé pour exécution ultra-rapide.
"""

import rclpy
from rclpy.node import Node
from moveit_msgs.msg import DisplayTrajectory
import json
import time
import os
import numpy as np
from scipy.interpolate import CubicSpline

class SmartTrajectoryProcessor(Node):
    """
    Bridge qui fait TOUS les calculs et optimisations d'avance.
    """
    
    def __init__(self):
        super().__init__('smart_trajectory_processor')
        
        # Output files
        self.output_file = '/tmp/moveit_smart_trajectory.json'
        
        # Processing settings
        self.interpolation_dt = 0.1  # 100ms steps (plus gros pas = moins de micro-mouvements)
        self.skip_threshold = 1.0  # Skip waypoints < 1.0° movement (BEAUCOUP plus agressif)
        self.min_speed = 500  # Vitesse minimale à 500
        self.max_speed = 900  # Vitesse maximale augmentée
        
        # Trajectory tracking
        self.last_trajectory_time = 0
        
        # Subscribe to MoveIt trajectory display
        self.trajectory_subscription = self.create_subscription(
            DisplayTrajectory,
            '/display_planned_path',
            self.trajectory_callback,
            10
        )
        
        print("[SmartProcessor] 🧠 Bridge intelligent démarré")
        print(f"[SmartProcessor] Calcule: positions + vitesses + optimisations")
        print(f"[SmartProcessor] Fichier de sortie: {self.output_file}")
        print("[SmartProcessor] Waiting for MoveIt trajectories...")
        
    def trajectory_callback(self, msg):
        """
        Callback principal : calcule TOUT et stocke dans un JSON optimisé.
        """
        try:
            if not msg.trajectory or len(msg.trajectory) == 0:
                return
                
            trajectory = msg.trajectory[0]
            if not trajectory.joint_trajectory.points:
                return
                
            current_time = time.time()
            
            # Nouvelle trajectoire si plus de 2 secondes depuis la dernière
            if current_time - self.last_trajectory_time > 2.0:
                print(f"\n[SmartProcessor] 🆕 NOUVELLE TRAJECTOIRE - CALCUL INTELLIGENT EN COURS...")
                
                # Étape 1: Extraire les waypoints bruts
                raw_waypoints = self._extract_waypoints(trajectory)
                print(f"[SmartProcessor] 📊 Waypoints bruts: {len(raw_waypoints)}")
                
                # Étape 2: Optimiser (skip waypoints similaires)
                optimized_waypoints = self._optimize_waypoints(raw_waypoints)
                print(f"[SmartProcessor] 🚀 Waypoints optimisés: {len(optimized_waypoints)} (skipped: {len(raw_waypoints) - len(optimized_waypoints)})")
                
                # Étape 3: Interpolation globale
                interpolated_trajectory = self._global_interpolation(optimized_waypoints)
                print(f"[SmartProcessor] 🧮 Points interpolés: {len(interpolated_trajectory)}")
                
                # Étape 4: Calcul des vitesses adaptatives
                final_trajectory = self._calculate_adaptive_speeds(interpolated_trajectory)
                print(f"[SmartProcessor] ⚡ Vitesses calculées pour {len(final_trajectory)} points")
                
                # Étape 4.5: NOUVEAU - Filtrage final pour éliminer les micro-mouvements
                ultra_filtered_trajectory = self._final_movement_filter(final_trajectory)
                print(f"[SmartProcessor] 🎯 Filtrage final: {len(ultra_filtered_trajectory)} points (éliminé {len(final_trajectory) - len(ultra_filtered_trajectory)} micro-mouvements)")
                
                # Étape 5: Sauvegarder le JSON final optimisé
                self._save_smart_trajectory(ultra_filtered_trajectory, trajectory.joint_trajectory.joint_names, current_time)
                
                print(f"[SmartProcessor] ✅ TRAJECTOIRE INTELLIGENTE PRÊTE!")
                print("=" * 60)
                
                self.last_trajectory_time = current_time
                
        except Exception as e:
            print(f"[SmartProcessor] ❌ Erreur: {e}")
    
    def _extract_waypoints(self, trajectory):
        """Extrait les waypoints bruts et CONVERTIT RADIANS → DEGRÉS."""
        waypoints = []
        for i, point in enumerate(trajectory.joint_trajectory.points):
            # Convertir les positions de radians vers degrés
            positions_degrees = [pos * 180.0 / 3.14159265359 for pos in point.positions]
            
            waypoint = {
                'positions': positions_degrees,  # Maintenant en degrés
                'time_from_start': point.time_from_start.sec + point.time_from_start.nanosec * 1e-9,
                'waypoint_index': i
            }
            waypoints.append(waypoint)
        return waypoints
    
    def _optimize_waypoints(self, waypoints):
        """Optimise en skippant les waypoints trop similaires."""
        if len(waypoints) <= 2:
            return waypoints
            
        optimized = [waypoints[0]]  # Toujours garder le premier
        
        for i in range(1, len(waypoints)):
            current_pos = waypoints[i]['positions']
            last_pos = optimized[-1]['positions']
            
            # Calculer le mouvement maximum
            max_movement = max(abs(current_pos[j] - last_pos[j]) for j in range(len(current_pos)))
            
            # Garder si mouvement significatif OU si c'est le dernier waypoint
            if max_movement > self.skip_threshold or i == len(waypoints) - 1:
                optimized.append(waypoints[i])
        
        return optimized
    
    def _global_interpolation(self, waypoints):
        """Interpolation globale avec cubic splines."""
        if len(waypoints) < 2:
            return waypoints
            
        # Extraire times et positions
        times = np.array([wp['time_from_start'] for wp in waypoints])
        positions = np.array([wp['positions'] for wp in waypoints])
        
        # Gérer le cas où les temps sont tous zéro
        if np.all(times == 0):
            total_duration = len(waypoints) * 1.0  # 1.0s par waypoint (plus lent mais mouvements plus grands)
            times = np.linspace(0, total_duration, len(waypoints))
        
        total_duration = times[-1] - times[0]
        if total_duration <= 0:
            return waypoints
            
        # Générer MOINS de points pour des mouvements plus grands
        num_steps = max(10, int(total_duration / self.interpolation_dt))  # Minimum 10 steps
        interpolation_times = np.linspace(times[0], times[-1], num_steps)
        
        # Interpolation cubic spline pour chaque joint
        num_joints = len(positions[0])
        interpolated_positions = np.zeros((num_steps, num_joints))
        
        for joint_idx in range(num_joints):
            joint_positions = positions[:, joint_idx]
            if len(waypoints) >= 4:  # Cubic spline si assez de points
                cs = CubicSpline(times, joint_positions, bc_type='natural')
                interpolated_positions[:, joint_idx] = cs(interpolation_times)
            else:  # Interpolation linéaire sinon
                interpolated_positions[:, joint_idx] = np.interp(interpolation_times, times, joint_positions)
        
        # Construire la trajectoire interpolée
        interpolated_trajectory = []
        for i in range(num_steps):
            step = {
                'positions': interpolated_positions[i].tolist(),
                'time': interpolation_times[i],
                'step_index': i
            }
            interpolated_trajectory.append(step)
        
        return interpolated_trajectory
    
    def _calculate_adaptive_speeds(self, trajectory):
        """Calcule les vitesses adaptatives pour chaque step."""
        if len(trajectory) <= 1:
            return trajectory
            
        for i in range(len(trajectory)):
            current_pos = trajectory[i]['positions']
            
            if i == 0:
                # Premier point: vitesse élevée pour démarrer
                next_pos = trajectory[i + 1]['positions']
                movement = max(abs(next_pos[j] - current_pos[j]) for j in range(len(current_pos)))
            elif i == len(trajectory) - 1:
                # Dernier point: vitesse modérée pour finir
                prev_pos = trajectory[i - 1]['positions']
                movement = max(abs(current_pos[j] - prev_pos[j]) for j in range(len(current_pos)))
            else:
                # Point intermédiaire: regarder mouvement vers le suivant
                next_pos = trajectory[i + 1]['positions']
                movement = max(abs(next_pos[j] - current_pos[j]) for j in range(len(current_pos)))
            
            # VITESSES ADAPTATIVES pour mouvements plus grands
            if movement < 0.5:
                speed = self.min_speed  # Petit mouvement: vitesse minimale (500)
            elif movement < 1.0:
                speed = int(self.min_speed + (movement / 1.0) * 100)  # 500-600
            elif movement < 2.0:
                speed = int(600 + (movement / 2.0) * 150)  # 600-750
            elif movement < 5.0:
                speed = int(750 + (movement / 5.0) * 150)  # 750-900
            else:
                speed = self.max_speed  # Grand mouvement: vitesse maximale (900)
            
            # Ajouter les paramètres calculés
            trajectory[i]['speed'] = min(max(speed, self.min_speed), self.max_speed)
            trajectory[i]['movement_size'] = movement
            trajectory[i]['wait_time'] = self.interpolation_dt  # Temps d'attente fixe
        
        return trajectory
    
    def _final_movement_filter(self, trajectory):
        """
        Filtrage FINAL pour éliminer les micro-mouvements après interpolation.
        Garde seulement les points avec des mouvements significatifs.
        """
        if len(trajectory) <= 2:
            return trajectory
            
        filtered = [trajectory[0]]  # Toujours garder le premier
        min_significant_movement = 0.3  # Mouvement minimum significatif en degrés
        
        for i in range(1, len(trajectory)):
            current_pos = trajectory[i]['positions']
            last_pos = filtered[-1]['positions']
            
            # Calculer le mouvement réel
            max_joint_movement = max(abs(current_pos[j] - last_pos[j]) for j in range(len(current_pos)))
            
            # Garder seulement si mouvement significatif OU si c'est le dernier point
            if max_joint_movement >= min_significant_movement or i == len(trajectory) - 1:
                # Recalculer la vitesse basée sur le nouveau mouvement
                trajectory[i]['movement_size'] = max_joint_movement
                
                # Ajuster la vitesse selon le vrai mouvement
                if max_joint_movement < 1.0:
                    trajectory[i]['speed'] = 600
                elif max_joint_movement < 3.0:
                    trajectory[i]['speed'] = 750
                else:
                    trajectory[i]['speed'] = 900
                
                filtered.append(trajectory[i])
        
        return filtered
    
    def _save_smart_trajectory(self, trajectory, joint_names, timestamp):
        """Sauvegarde la trajectoire intelligente complète."""
        # Statistiques
        total_movements = [step['movement_size'] for step in trajectory]
        avg_movement = np.mean(total_movements) if total_movements else 0
        max_movement = max(total_movements) if total_movements else 0
        
        speeds_used = [step['speed'] for step in trajectory]
        avg_speed = np.mean(speeds_used) if speeds_used else 0
        
        smart_data = {
            'timestamp': timestamp,
            'joint_names': list(joint_names),
            'trajectory_steps': trajectory,
            'metadata': {
                'total_steps': len(trajectory),
                'total_duration': trajectory[-1]['time'] - trajectory[0]['time'] if len(trajectory) > 1 else 0,
                'interpolation_dt': self.interpolation_dt,
                'avg_movement': avg_movement,
                'max_movement': max_movement,
                'avg_speed': avg_speed,
                'speed_range': [self.min_speed, self.max_speed],
                'processing_complete': True,
                'ready_for_execution': True
            }
        }
        
        # Écrire le fichier JSON optimisé
        with open(self.output_file, 'w') as f:
            json.dump(smart_data, f, indent=2)
        
        # Afficher les statistiques
        print(f"[SmartProcessor] 📊 STATISTIQUES CALCULÉES:")
        print(f"   • Total steps: {len(trajectory)}")
        print(f"   • Durée totale: {smart_data['metadata']['total_duration']:.1f}s")
        print(f"   • Mouvement moyen: {avg_movement:.2f}°")
        print(f"   • Mouvement max: {max_movement:.2f}°")
        print(f"   • Vitesse moyenne: {avg_speed:.0f}")
        print(f"   • Fichier: {self.output_file}")

def main(args=None):
    rclpy.init(args=args)
    
    # Clear old data file
    output_file = '/tmp/moveit_smart_trajectory.json'
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"[SmartProcessor] 🗑️ Ancien fichier supprimé")
    
    processor = SmartTrajectoryProcessor()
    
    try:
        rclpy.spin(processor)
    except KeyboardInterrupt:
        print("\n[SmartProcessor] CTRL-C détecté, arrêt...")
    finally:
        processor.destroy_node()
        rclpy.shutdown()
        print("[SmartProcessor] Processor arrêté.")

if __name__ == '__main__':
    main()
