#!/usr/bin/env python3
"""
Robot executeur ULTRA-RAPIDE qui lit un JSON pré-calculé et exécute tout.
Plus de calculs en temps réel - juste de l'exécution pure!
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

class SmartTrajectoryExecutor:
    """
    Exécuteur qui lit un JSON pré-calculé et exécute ULTRA-RAPIDEMENT.
    Toutes les optimisations et calculs ont déjà été faits!
    """
    
    def __init__(self, smart_data_file='/tmp/moveit_smart_trajectory.json'):
        self.smart_data_file = smart_data_file
        self.latest_trajectory = None
        self.latest_timestamp = 0
        self.data_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        
    def start_reading(self, update_interval=0.1):
        """Démarre la lecture du fichier JSON intelligent."""
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, args=(update_interval,))
        self.reader_thread.daemon = True
        self.reader_thread.start()
        print(f"[SmartExecutor] 📖 Lecture démarrée: {self.smart_data_file}")
        
    def _read_loop(self, update_interval):
        """Loop de lecture du JSON intelligent."""
        startup_delay = 3.0  # 3 secondes avant traitement
        startup_time = time.time()
        
        while self.running:
            try:
                # Skip pendant le délai de démarrage
                if time.time() - startup_time < startup_delay:
                    time.sleep(0.5)
                    continue
                    
                if os.path.exists(self.smart_data_file):
                    with open(self.smart_data_file, 'r') as f:
                        data = json.load(f)
                    
                    # Vérifier si c'est de nouvelles données
                    if data.get('timestamp', 0) > self.latest_timestamp:
                        if data.get('metadata', {}).get('ready_for_execution', False):
                            with self.data_lock:
                                self.latest_trajectory = data
                                self.latest_timestamp = data.get('timestamp', 0)
                            
                            steps = len(data.get('trajectory_steps', []))
                            duration = data.get('metadata', {}).get('total_duration', 0)
                            print(f"[SmartExecutor] 🆕 TRAJECTOIRE INTELLIGENTE PRÊTE!")
                            print(f"[SmartExecutor] {steps} steps, {duration:.1f}s, tout pré-calculé!")
                        
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                pass
            
            time.sleep(update_interval)
    
    def get_latest_smart_trajectory(self):
        """Récupère la dernière trajectoire intelligente."""
        with self.data_lock:
            if self.latest_trajectory:
                return self.latest_trajectory.copy()
        return None
    
    def stop_reading(self):
        """Arrête la lecture."""
        self.running = False
        if self.reader_thread:
            self.reader_thread.join()

def map_moveit_joints_to_simulation(moveit_positions, moveit_joint_names, sim_joint_count=6):
    """
    Mapping MoveIt -> simulation avec compensation d'offset.
    Les positions sont DÉJÀ en degrés (converties dans le bridge).
    """
    if not moveit_positions or not moveit_joint_names:
        return None
        
    # Noms des joints Lynx SES900 attendus
    lynx_joint_names = [
        'joint_1',      # Joint 0 (Base rotation)
        'joint_2',      # Joint 1 (Shoulder)
        'joint_3',      # Joint 2 (Upper arm)
        'joint_4',      # Joint 3 (Forearm)
        'joint_5',      # Joint 4 (Wrist)
        'joint_6'       # Joint 5 (End-effector rotation)
    ]
    
    # Offsets de compensation (en degrés)
    joint_offsets = [0, 0, 0, 0, 0, 0]
    
    # Créer le mapping
    joint_dict = dict(zip(moveit_joint_names, moveit_positions))
    
    # Mapper vers l'ordre de simulation
    simulation_positions = []
    for i, joint_name in enumerate(lynx_joint_names):
        if joint_name in joint_dict:
            # Les positions sont DÉJÀ en degrés depuis le bridge
            angle_degrees = joint_dict[joint_name]
            compensated_position = angle_degrees + joint_offsets[i]
            simulation_positions.append(compensated_position)
        else:
            print(f"[Mapping] Warning: Joint {joint_name} not found")
            return None
            
    return simulation_positions

if __name__ == '__main__':
    # Supprimer l'ancien fichier pour éviter l'exécution immédiate
    smart_data_file = '/tmp/moveit_smart_trajectory.json'
    if os.path.exists(smart_data_file):
        print(f"[Main] 🗑️ Suppression ancien fichier: {smart_data_file}")
        try:
            os.remove(smart_data_file)
        except Exception as e:
            print(f"[Main] Warning: {e}")
    
    # Initialiser le robot PyBullet
    robo = SimRobot()
    if not robo.init_bus():
        print("[Main] ❌ Échec d'ouverture simulation.")
        exit(1)
    robo.init_motors()

    # Position initiale du robot
    initial_joint_angles = robo.get_Position()
    if initial_joint_angles:
        initial_positions = [angle[0] if angle[0] is not None else 0.0 for angle in initial_joint_angles]
        print(f"[Main] Position initiale: {[f'{pos:.2f}°' for pos in initial_positions]}")
    else:
        initial_positions = [0.0] * 6
        print("[Main] Warning: Position home assumée")
    
    # Infos PyBullet
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
    
    # Initialiser l'exécuteur intelligent
    smart_executor = SmartTrajectoryExecutor()
    smart_executor.start_reading(update_interval=0.1)
    
    print("[Main] 🤖 ROBOT EXÉCUTEUR INTELLIGENT DÉMARRÉ")
    print("[Main] Fonctionnalités:")
    print("  - 🧠 Lecture de trajectoires pré-calculées avec vitesses adaptatives")
    print("  - ⚡ Exécution ULTRA-RAPIDE (plus de calculs en temps réel)")
    print("  - 🎯 Vitesses optimisées pour chaque step")
    print("  - 🛡️ Sécurité et limites articulaires")
    print("  - ⏱️ Délai de démarrage: 3 secondes")
    print("[Main] Planifiez dans MoveIt et regardez l'exécution intelligente!")
    
    try:
        trajectory_count = 0
        current_execution = False
        
        while True:
            if watchdog._exception_event.is_set():
                print("\n[Main] ⚠️ Watchdog a détecté une exception critique.")
                robo.enter_emergency_recovery()
                break
            
            # Chercher une nouvelle trajectoire intelligente
            smart_trajectory = smart_executor.get_latest_smart_trajectory()
            
            if smart_trajectory and not current_execution:
                trajectory_steps = smart_trajectory.get('trajectory_steps', [])
                joint_names = smart_trajectory.get('joint_names', [])
                metadata = smart_trajectory.get('metadata', {})
                
                if len(trajectory_steps) >= 2:
                    trajectory_count += 1
                    current_execution = True
                    
                    print(f"\n[Main] ===== EXÉCUTION INTELLIGENTE #{trajectory_count} =====")
                    print(f"[Main] 🧠 Trajectoire pré-calculée: {len(trajectory_steps)} steps")
                    print(f"[Main] ⏱️ Durée prévue: {metadata.get('total_duration', 0):.1f}s")
                    print(f"[Main] 🎯 Vitesse moyenne: {metadata.get('avg_speed', 0):.0f}")
                    print(f"[Main] 📐 Mouvement moyen: {metadata.get('avg_movement', 0):.2f}°")
                    print(f"[Main] 🚀 DÉBUT D'EXÉCUTION ULTRA-RAPIDE...")
                    
                    execution_start_time = time.time()
                    successful_steps = 0
                    
                    # EXÉCUTION ULTRA-RAPIDE: plus de calculs, juste des commandes
                    for i, step in enumerate(trajectory_steps):
                        step_positions = step['positions']
                        step_speed = step['speed']
                        step_wait = step['wait_time']
                        
                        # Mapper vers la simulation
                        sim_positions = map_moveit_joints_to_simulation(step_positions, joint_names)
                        
                        if sim_positions:
                            # Appliquer les limites de sécurité
                            safe_positions = []
                            for j, angle in enumerate(sim_positions):
                                if j < len(rl_config.JOINT_LIMITS):
                                    min_limit, max_limit = rl_config.JOINT_LIMITS[j]
                                    clamped_angle = np.clip(angle, min_limit, max_limit)
                                    safe_positions.append(float(clamped_angle))
                                else:
                                    safe_positions.append(float(angle))
                            
                            try:
                                # COMMANDE ROBOT avec vitesse pré-calculée
                                robo.move_abs_with_speed(safe_positions, speed=step_speed)
                                
                                # Step simulation
                                with pybullet_api_lock:
                                    pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                                
                                successful_steps += 1
                                
                                # Affichage du progrès (moins fréquent pour la vitesse)
                                if i % 20 == 0 or i == len(trajectory_steps) - 1:
                                    progress = (i + 1) / len(trajectory_steps) * 100
                                    print(f"[Main] Step {i+1}/{len(trajectory_steps)} ({progress:.1f}%) - Vitesse: {step_speed}")
                                
                                # Attendre selon le timing pré-calculé
                                time.sleep(step_wait)
                                
                            except Exception as e:
                                print(f"[Main] ❌ Erreur step {i}: {e}")
                                break
                        else:
                            print(f"[Main] ❌ Mapping failed pour step {i}")
                            break
                    
                    # Exécution terminée
                    total_execution_time = time.time() - execution_start_time
                    predicted_time = metadata.get('total_duration', 0)
                    time_diff = total_execution_time - predicted_time
                    
                    print(f"\n[Main] ✅ EXÉCUTION INTELLIGENTE TERMINÉE!")
                    print(f"[Main] Steps exécutés: {successful_steps}/{len(trajectory_steps)}")
                    print(f"[Main] Temps réel: {total_execution_time:.2f}s")
                    print(f"[Main] Temps prévu: {predicted_time:.2f}s")
                    print(f"[Main] Différence: {time_diff:+.2f}s")
                    
                    if successful_steps == len(trajectory_steps):
                        print(f"[Main] 🎉 SUCCÈS COMPLET! Toutes les étapes exécutées.")
                    else:
                        print(f"[Main] ⚠️ Exécution partielle: {successful_steps}/{len(trajectory_steps)}")
                    
                    # Position finale de l'effecteur
                    if sim_data_manager.latest_relative_pos is not None:
                        pos = sim_data_manager.latest_relative_pos
                        print(f'[Main] Position finale EEF: X={pos[0]:.4f}, Y={pos[1]:.4f}, Z={pos[2]:.4f}')
                        
                    # Angles articulaires finaux
                    final_joint_angles = robo.get_Position()
                    if final_joint_angles:
                        angles_str = [f'{angle[0]:.2f}°' if angle[0] is not None else 'N/A' 
                                    for angle in final_joint_angles]
                        print(f"[Main] Angles finaux: {angles_str}")
                    
                    current_execution = False
                    print("=" * 80)
            
            # Toujours faire un step de simulation
            with pybullet_api_lock:
                pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                
            time.sleep(0.1)  # Loop principale à 10Hz
            
    except KeyboardInterrupt:
        print("\n[Main] CTRL-C détecté. Arrêt...")
        robo.enter_emergency_recovery()
    except Exception as e:
        print(f"[Main] Exception dans la loop principale: {e}")
        robo.enter_emergency_recovery()
    finally:
        print("[Main] Nettoyage...")
        smart_executor.stop_reading()
        watchdog.stop()
        robo.shutdown()
        print("[Main] Arrêt complet.")
