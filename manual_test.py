#!/usr/bin/env python3
"""
Test simple pour vérifier que le robot suit bien les commandes MoveIt
"""

import json
import time
import numpy as np

# Simuler des commandes MoveIt
test_commands = [
    # Position home MoveIt
    {
        'joint_positions': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Déjà avec compensation
        'joint_names': ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'],
        'target_pose': None,
        'timestamp': time.time()
    },
    # Position test 1
    {
        'joint_positions': [45.0, 90.0, 30.0, 0.0, 0.0, 0.0],
        'joint_names': ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'],
        'target_pose': None,
        'timestamp': time.time()
    },
    # Position test 2
    {
        'joint_positions': [0.0, 45.0, 45.0, 30.0, 0.0, 0.0],
        'joint_names': ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'],
        'target_pose': None,
        'timestamp': time.time()
    },
    # Position test 3
    {
        'joint_positions': [-45.0, 90.0, 0.0, -30.0, 0.0, 0.0],
        'joint_names': ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'],
        'target_pose': None,
        'timestamp': time.time()
    }
]

data_file = '/tmp/moveit_to_pybullet_data.json'

print("🧪 Test de simulation MoveIt → PyBullet")
print("📋 Envoi de commandes de test...")

for i, cmd in enumerate(test_commands):
    print(f"\n[Test] Envoi commande {i+1}: {[f'{pos:.1f}°' for pos in cmd['joint_positions']]}")
    
    # Mettre à jour le timestamp
    cmd['timestamp'] = time.time()
    
    # Écrire dans le fichier
    with open(data_file, 'w') as f:
        json.dump(cmd, f)
    
    # Attendre avant la prochaine commande
    time.sleep(3)

print("\n✅ Test terminé!")
print("💡 Le robot PyBullet devrait avoir bougé selon les commandes")
