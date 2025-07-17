# Synchronisation MoveIt → PyBullet

Ce système permet de synchroniser les mouvements d'un robot UR5 dans MoveIt avec la simulation PyBullet en temps réel.

## Architecture

```
MoveIt (ROS2) → ROS Bridge Node → JSON File → PyBullet Simulation
```

## Fichiers principaux

1. **`UR_WS/src/ik_move_cpp/src/moveit_to_pybullet_bridge.py`** - Nœud ROS qui écoute les joint states
2. **`real_robot/main_sim_ros_bridge.py`** - Simulation PyBullet qui lit les commandes
3. **`start_moveit_pybullet_sync.sh`** - Script de démarrage automatique

## Utilisation

### Méthode 1 : Démarrage manuel (3 terminaux)

#### Terminal 1 : Démarrer MoveIt
```bash
cd ~/Documents/GitHub/adaptive_robot_planning/UR_WS
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch ur_simulation_gazebo ur_sim_moveit.launch.py
```

#### Terminal 2 : Démarrer le bridge ROS
```bash
cd ~/Documents/GitHub/adaptive_robot_planning/UR_WS/src/ik_move_cpp/src
source /opt/ros/humble/setup.bash
/usr/bin/python3 moveit_to_pybullet_bridge.py
```

#### Terminal 3 : Démarrer PyBullet
```bash
cd ~/Documents/GitHub/adaptive_robot_planning/real_robot
python main_sim_ros_bridge.py
```

### Méthode 2 : Utiliser le script automatique
```bash
cd ~/Documents/GitHub/adaptive_robot_planning
./start_moveit_pybullet_sync.sh
```

## Fonctionnement

1. **MoveIt** publie les joint states sur `/joint_states`
2. **Le bridge ROS** convertit les positions (radians → degrés) et les sauvegarde dans `/tmp/moveit_to_pybullet_data.json`
3. **PyBullet** lit ce fichier et applique les mouvements au robot simulé

## Données échangées

Le fichier JSON contient :
```json
{
  "joint_positions": [12.5, -30.0, 45.0, 0.0, 90.0, -15.0],
  "joint_names": ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"],
  "target_pose": {
    "position": [0.5, 0.2, 0.3],
    "orientation": [0.0, 0.0, 0.0, 1.0]
  },
  "timestamp": 1752743543.037
}
```

## Mapping des joints

| MoveIt Joint Name    | PyBullet Joint ID | Description |
|---------------------|-------------------|-------------|
| shoulder_pan_joint  | 0                 | Base rotation |
| shoulder_lift_joint | 1                 | Shoulder lift |
| elbow_joint         | 2                 | Elbow |
| wrist_1_joint       | 3                 | Wrist 1 |
| wrist_2_joint       | 4                 | Wrist 2 |
| wrist_3_joint       | 5                 | Wrist 3 |

## Sécurité

- Le système SafetyWatchdog surveille les limites des joints
- Arrêt d'urgence avec Ctrl+C
- Détection des collisions avec la table

## Dépannage

### Problème : "No module named 'catkin_pkg'"
- Utiliser Python système : `/usr/bin/python3`
- Sourcer ROS : `source /opt/ros/humble/setup.bash`

### Problème : "Pas de données MoveIt"
- Vérifier que MoveIt est démarré
- Vérifier les topics ROS : `ros2 topic list`
- Vérifier le fichier JSON : `cat /tmp/moveit_to_pybullet_data.json`

### Problème : "Simulation PyBullet figée"
- Vérifier que le bridge ROS fonctionne
- Redémarrer la simulation avec Ctrl+C puis relancer

## Contrôle du robot

Une fois le système démarré :
1. Utilisez **RViz** pour planifier des mouvements
2. Définissez une pose cible pour l'end-effector
3. Planifiez et exécutez le mouvement
4. **Le robot PyBullet suivra automatiquement !**

## Logs utiles

- `[ROSBridge] Updated joint positions` - Nouvelles positions reçues
- `[Main] Moving to:` - Commande envoyée à PyBullet
- `[Main] EEF position:` - Position de l'end-effector
- `[Watchdog] Joint Limits:` - Limites de sécurité actives
