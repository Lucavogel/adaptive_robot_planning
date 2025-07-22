#!/usr/bin/env python3
"""
Simulation PyBullet qui exécute TOUS les waypoints point par point.
Attend que la trajectoire MoveIt soit COMPLÈTE puis exécute waypoint par waypoint.
"""

import logging
import numpy as np
import time
import threading
import json
import os

from sim_robot import SimRobot
from safety import SafetyWatchdogSim
from sim_sensor import SimNatNetDataHandler
import rl_config

class AllPointsTrajectoryReader:
    """
    Lecteur qui lit TOUTE la trajectoire MoveIt et l'exécute point par point.
    """
    
    def __init__(self, data_file_path='/tmp/moveit_all_points_trajectory.json'):
        self.data_file_path = data_file_path
        self.current_trajectory = None
        self.current_waypoint_index = 0
        self.trajectory_complete = False
        self.data_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        self.last_read_timestamp = 0
        self.last_executed_positions = None  # Pour skip les waypoints similaires
        self.skip_threshold = 0.5  # Skip si mouvement < 0.5°
        self.skipped_count = 0
        
    def start_reading(self, update_interval=0.1):
        """Démarre la lecture des trajectoires complètes."""
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, args=(update_interval,))
        self.reader_thread.daemon = True
        self.reader_thread.start()
        print(f"[AllPointsReader] 📖 Lecture démarrée: {self.data_file_path}")
        
    def _read_loop(self, update_interval):
        """Boucle de lecture des trajectoires complètes."""
        startup_delay = 2.0
        startup_time = time.time()
        
        while self.running:
            try:
                # Delay de démarrage
                if time.time() - startup_time < startup_delay:
                    time.sleep(0.5)
                    continue
                    
                if os.path.exists(self.data_file_path):
                    with open(self.data_file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Vérifier si c'est une nouvelle trajectoire complète
                    if (data.get('timestamp', 0) > self.last_read_timestamp and 
                        data.get('trajectory_complete', False)):
                        
                        with self.data_lock:
                            self.current_trajectory = data
                            self.current_waypoint_index = 0
                            self.trajectory_complete = False
                            self.last_read_timestamp = data.get('timestamp', 0)
                            self.last_executed_positions = None  # Reset pour nouvelle trajectoire
                            self.skipped_count = 0
                        
                        waypoints = data.get('trajectory_waypoints', [])
                        print(f"[AllPointsReader] 🎯 NOUVELLE TRAJECTOIRE CHARGÉE!")
                        print(f"[AllPointsReader] Total waypoints: {len(waypoints)}")
                        print(f"[AllPointsReader] Durée totale: {data.get('total_duration', 0):.1f}s")
                        print(f"[AllPointsReader] 🚀 Skip automatique si mouvement < {self.skip_threshold}°")
                        
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            except Exception as e:
                print(f"[AllPointsReader] Erreur: {e}")
            
            time.sleep(update_interval)
    
    def get_next_waypoint(self):
        """Retourne le prochain waypoint à exécuter, en skippant les waypoints similaires."""
        with self.data_lock:
            if not self.current_trajectory:
                return None, None
                
            waypoints = self.current_trajectory.get('trajectory_waypoints', [])
            joint_names = self.current_trajectory.get('joint_names', [])
            
            # Boucle pour trouver un waypoint significativement différent
            while self.current_waypoint_index < len(waypoints):
                waypoint = waypoints[self.current_waypoint_index]
                current_positions = waypoint['positions']
                
                # Premier waypoint ou mouvement significatif détecté
                if (self.last_executed_positions is None or 
                    self._is_significant_movement(current_positions, self.last_executed_positions)):
                    
                    self.current_waypoint_index += 1
                    self.last_executed_positions = current_positions.copy()
                    return waypoint, joint_names
                else:
                    # Skip ce waypoint
                    self.current_waypoint_index += 1
                    self.skipped_count += 1
                    if self.skipped_count % 10 == 0:  # Log tous les 10 skips
                        print(f"[AllPointsReader] 🚀 Skipped {self.skipped_count} waypoints similaires")
            
            # Fin de trajectoire
            if not self.trajectory_complete:
                print(f"[AllPointsReader] ✅ TRAJECTOIRE TERMINÉE!")
                print(f"[AllPointsReader] Waypoints exécutés: {len(waypoints) - self.skipped_count}/{len(waypoints)}")
                print(f"[AllPointsReader] Waypoints skippés: {self.skipped_count}")
                self.trajectory_complete = True
            return None, None
    
    def _is_significant_movement(self, new_positions, last_positions):
        """Vérifie si le mouvement est significatif (> seuil)."""
        if not last_positions or len(new_positions) != len(last_positions):
            return True
            
        max_diff = max(abs(new_positions[i] - last_positions[i]) for i in range(len(new_positions)))
        return max_diff > self.skip_threshold
    
    def is_trajectory_complete(self):
        """Vérifie si la trajectoire est terminée."""
        with self.data_lock:
            return self.trajectory_complete
    
    def get_trajectory_progress(self):
        """Retourne le progrès de la trajectoire (en comptant les skips)."""
        with self.data_lock:
            if not self.current_trajectory:
                return 0, 0, 0.0
                
            waypoints = self.current_trajectory.get('trajectory_waypoints', [])
            total = len(waypoints)
            current = self.current_waypoint_index
            executed = current - self.skipped_count
            progress = (current / total) * 100 if total > 0 else 0
            
            return executed, total, progress
    
    def stop_reading(self):
        """Arrête la lecture."""
        self.running = False
        if self.reader_thread:
            self.reader_thread.join()

def map_moveit_joints_to_simulation(moveit_positions, moveit_joint_names, sim_joint_count=6):
    """
    Mappe les joints MoveIt vers l'ordre de la simulation.
    """
    if not moveit_positions or not moveit_joint_names:
        return None
        
    # Noms des joints Lynx SES900 attendus dans MoveIt
    lynx_joint_names = [
        'joint_1',      # Joint 0 (Base rotation)
        'joint_2',      # Joint 1 (Shoulder)
        'joint_3',      # Joint 2 (Upper arm)
        'joint_4',      # Joint 3 (Forearm)
        'joint_5',      # Joint 4 (Wrist)
        'joint_6'       # Joint 5 (End-effector rotation)
    ]
    
    # Compensation d'offset pour la position home de la simulation
    joint_offsets = [0, 0, 0, 0, 0, 0]
    
    # Créer le mapping des noms de joints MoveIt vers les positions
    joint_dict = dict(zip(moveit_joint_names, moveit_positions))
    
    # Mapper vers l'ordre de la simulation avec compensation d'offset
    simulation_positions = []
    for i, joint_name in enumerate(lynx_joint_names):
        if joint_name in joint_dict:
            compensated_position = joint_dict[joint_name] + joint_offsets[i]
            simulation_positions.append(compensated_position)
        else:
            print(f"[Mapping] Warning: Joint {joint_name} not found in MoveIt data")
            return None
            
    return simulation_positions

if __name__ == '__main__':
    # Nettoyer l'ancien fichier de données
    data_file_path = '/tmp/moveit_all_points_trajectory.json'
    if os.path.exists(data_file_path):
        print(f"[Main] 🗑️ Suppression ancien fichier: {data_file_path}")
        try:
            os.remove(data_file_path)
        except Exception as e:
            print(f"[Main] Warning: {e}")
    
    # Initialiser le robot PyBullet
    robo = SimRobot()
    if not robo.init_bus():
        print("[Main] Failed to open simulation. Exiting.")
        exit(1)
    robo.init_motors()

    # Obtenir la position initiale du robot
    initial_joint_angles = robo.get_Position()
    if initial_joint_angles:
        initial_positions = [angle[0] if angle[0] is not None else 0.0 for angle in initial_joint_angles]
        print(f"[Main] Position initiale: {[f'{pos:.1f}°' for pos in initial_positions]}")
    else:
        initial_positions = [0.0] * 6
        print("[Main] Warning: Position initiale non disponible")
    
    # Obtenir les informations PyBullet
    pybullet_api = robo.get_pybullet_api()
    physics_client_id = robo.get_physics_client_id()
    robot_id = robo.get_robot_id()
    ee_link_id = robo.get_end_effector_link_id()
    pybullet_api_lock = robo.get_pybullet_api_lock()

    # Initialiser le capteur simulé
    sim_data_manager = SimNatNetDataHandler(
        p_api=pybullet_api,
        physics_client_id=physics_client_id,
        robot_id=robot_id,
        end_effector_link_id=ee_link_id,
        pybullet_api_lock=pybullet_api_lock,
        verbose=False
    )
    
    # Initialiser le watchdog de sécurité
    watchdog = SafetyWatchdogSim(
        robot_controller=robo,
        natnet_data_handler=sim_data_manager,
        joint_limits=rl_config.JOINT_LIMITS,
        marker_radii=rl_config.MARKER_RADII,
    )
    robo.joint_watchdog = watchdog
    watchdog.start(check_interval=rl_config.WATCHDOG_INTERVAL)
    
    # Initialiser le lecteur de trajectoires
    trajectory_reader = AllPointsTrajectoryReader()
    trajectory_reader.start_reading(update_interval=0.1)
    
    print("[Main] 🤖 Robot PyBullet initialisé - EXÉCUTION POINT PAR POINT")
    print("[Main] Fonctionnalités:")
    print("  ✅ Attend que la trajectoire MoveIt soit COMPLÈTE")
    print("  ✅ Exécute TOUS les waypoints un par un")
    print("  ✅ Attend que chaque mouvement soit fini")
    print("  ✅ Affiche le progrès en temps réel")
    print("  ✅ Sécurité avec limites des joints")
    print("[Main] 📋 Planifiez une trajectoire dans MoveIt et regardez l'exécution!")
    print("=" * 70)
    
    try:
        trajectory_count = 0
        waypoint_execution_time = 0.4  # 400ms par waypoint (plus rapide maintenant qu'on skip)
        movement_speed = 600  # Vitesse plus rapide car on exécute moins de waypoints
        
        while True:
            if watchdog._exception_event.is_set():
                print("\n[Main] Watchdog a détecté une exception critique. Arrêt.")
                robo.enter_emergency_recovery()
                break
            
            # Obtenir le prochain waypoint
            waypoint_data, joint_names = trajectory_reader.get_next_waypoint()
            
            if waypoint_data and joint_names:
                trajectory_count += 1 if trajectory_reader.current_waypoint_index == 1 else 0
                
                current_wp, total_wp, progress = trajectory_reader.get_trajectory_progress()
                
                print(f"\n[Main] ===== WAYPOINT SIGNIFICATIF {current_wp}/{total_wp} ({progress:.1f}%) =====")
                
                # Extraire les données du waypoint
                moveit_positions = waypoint_data['positions']
                time_from_start = waypoint_data['time_from_start']
                waypoint_index = waypoint_data['waypoint_index']
                
                print(f"[Main] Waypoint #{waypoint_index}: {[f'{pos:.1f}°' for pos in moveit_positions]}")
                print(f"[Main] Temps depuis début: {time_from_start:.2f}s")
                
                # Calculer le mouvement depuis le dernier waypoint exécuté
                if hasattr(trajectory_reader, 'last_executed_positions') and trajectory_reader.last_executed_positions:
                    movement_diff = [abs(moveit_positions[i] - trajectory_reader.last_executed_positions[i]) 
                                   for i in range(len(moveit_positions))]
                    max_movement = max(movement_diff)
                    print(f"[Main] 📏 Mouvement depuis dernier: {[f'{diff:.1f}°' for diff in movement_diff]} (max: {max_movement:.1f}°)")
                
                # Mapper vers la simulation
                sim_positions = map_moveit_joints_to_simulation(moveit_positions, joint_names)
                
                if sim_positions:
                    # Appliquer les limites de sécurité
                    safe_positions = []
                    for j, angle in enumerate(sim_positions):
                        if j < len(rl_config.JOINT_LIMITS):
                            min_limit, max_limit = rl_config.JOINT_LIMITS[j]
                            clamped_angle = np.clip(angle, min_limit, max_limit)
                            safe_positions.append(float(clamped_angle))
                            
                            if abs(clamped_angle - angle) > 0.1:
                                print(f"[Main] ⚠️ Joint {j} limité: {angle:.1f}° → {clamped_angle:.1f}°")
                        else:
                            safe_positions.append(float(angle))
                    
                    print(f"[Main] 🎯 Exécution: {[f'{pos:.1f}°' for pos in safe_positions]}")
                    
                    # Envoyer la commande au robot avec vitesse plus lente
                    movement_start_time = time.time()
                    try:
                        robo.move_abs_with_speed(safe_positions, speed=movement_speed)  # Vitesse plus lente
                        
                        # Attendre que le mouvement soit terminé - PLUS LONG
                        time.sleep(waypoint_execution_time)
                        
                        movement_duration = time.time() - movement_start_time
                        print(f"[Main] ✅ Mouvement terminé en {movement_duration*1000:.0f}ms")
                        
                        # Afficher les différences de position pour debug
                        final_joint_angles = robo.get_Position()
                        if final_joint_angles:
                            final_angles = [angle[0] if angle[0] is not None else 0.0 for angle in final_joint_angles]
                            print(f"[Main] Position finale: {[f'{pos:.1f}°' for pos in final_angles]}")
                            
                            # Calculer et afficher le mouvement réalisé
                            if hasattr(robo, '_last_sent_positions'):
                                movement_diff = [abs(final_angles[i] - robo._last_sent_positions[i]) for i in range(len(final_angles))]
                                max_movement = max(movement_diff)
                                print(f"[Main] 📏 Mouvement réalisé: {[f'{diff:.1f}°' for diff in movement_diff]} (max: {max_movement:.1f}°)")
                            
                            # Stocker pour prochaine comparaison
                            robo._last_sent_positions = final_angles.copy()
                        
                        # Afficher la position end-effector
                        if sim_data_manager.latest_relative_pos is not None:
                            pos = sim_data_manager.latest_relative_pos
                            print(f'[Main] EEF: X={pos[0]:.3f}, Y={pos[1]:.3f}, Z={pos[2]:.3f}')
                        
                    except Exception as e:
                        print(f"[Main] ❌ Erreur mouvement: {e}")
                        continue
            
            else:
                # Pas de waypoint disponible
                if trajectory_reader.is_trajectory_complete():
                    current_wp, total_wp, progress = trajectory_reader.get_trajectory_progress()
                    if total_wp > 0:
                        print(f"\n[Main] 🎉 TRAJECTOIRE #{trajectory_count} TERMINÉE!")
                        print(f"[Main] Total exécuté: {current_wp-1}/{total_wp} waypoints")
                        print("=" * 70)
                else:
                    print("[Main] ⏳ Attente trajectoire MoveIt complète...")
            
            # Toujours faire un pas de simulation
            with pybullet_api_lock:
                pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                
            time.sleep(0.1)  # 10Hz main loop
            
    except KeyboardInterrupt:
        print("\n[Main] CTRL-C détecté. Arrêt...")
        robo.enter_emergency_recovery()
    except Exception as e:
        print(f"[Main] Exception: {e}")
        robo.enter_emergency_recovery()
    finally:
        print("[Main] Nettoyage...")
        trajectory_reader.stop_reading()
        watchdog.stop()
        robo.shutdown()
        print("[Main] Arrêt terminé.")
