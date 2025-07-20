#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'real_robot'))

from sim_robot import SimRobot
import time

def test_lynx_load():
    print("=== Test de chargement du robot Lynx SES900 ===")
    
    sim_robot = SimRobot()
    
    try:
        print("Initialisation de PyBullet...")
        success = sim_robot.init_bus()
        
        if not success:
            print("ERREUR: Échec de l'initialisation")
            return False
            
        print("✓ PyBullet initialisé avec succès")
        print(f"✓ Robot ID: {sim_robot.get_robot_id()}")
        print(f"✓ Joints contrôlés: {sim_robot._controlled_joint_indices}")
        print(f"✓ End-effector link ID: {sim_robot._end_effector_link_id}")
        
        print("Initialisation des moteurs...")
        sim_robot.init_motors()
        print(f"✓ {len(sim_robot._motors)} moteurs initialisés")
        
        print("Robot chargé avec succès!")
        
        # Test de mouvements simples
        print("\n=== Test des mouvements ===")
        
        # Position home (tous les joints à 0)
        print("1. Position home (tous les joints à 0°)...")
        home_position = [0, 0, 0, 0, 0, 0]
        sim_robot.move_abs(home_position)
        # Faire avancer la simulation pour voir le mouvement
        for _ in range(300):  # 3 secondes à 100Hz
            sim_robot.get_pybullet_api().stepSimulation(physicsClientId=sim_robot.get_physics_client_id())
            time.sleep(0.01)
        
        # Position de test 1
        print("2. Position test 1...")
        test_position_1 = [30, -45, 60, -30, 45, 0]
        sim_robot.move_abs(test_position_1)
        # Faire avancer la simulation
        for _ in range(300):  # 3 secondes à 100Hz
            sim_robot.get_pybullet_api().stepSimulation(physicsClientId=sim_robot.get_physics_client_id())
            time.sleep(0.01)
        
        # Position de test 2
        print("3. Position test 2...")
        test_position_2 = [-30, 45, -60, 30, -45, 90]
        sim_robot.move_abs(test_position_2)
        # Faire avancer la simulation
        for _ in range(300):  # 3 secondes à 100Hz
            sim_robot.get_pybullet_api().stepSimulation(physicsClientId=sim_robot.get_physics_client_id())
            time.sleep(0.01)
        
        # Retour à la position home
        print("4. Retour à la position home...")
        sim_robot.move_abs(home_position)
        # Faire avancer la simulation
        for _ in range(300):  # 3 secondes à 100Hz
            sim_robot.get_pybullet_api().stepSimulation(physicsClientId=sim_robot.get_physics_client_id())
            time.sleep(0.01)
        
        print("✓ Tests de mouvement terminés!")
        print("La simulation reste ouverte. Appuyez sur Ctrl+C pour fermer...")
        
        # Garder la simulation ouverte pour visualisation
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nFermeture par l'utilisateur")
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        sim_robot.shutdown()
        print("Simulation fermée")

if __name__ == "__main__":
    test_lynx_load()
