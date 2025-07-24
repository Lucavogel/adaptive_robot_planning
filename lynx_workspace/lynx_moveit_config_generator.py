#!/usr/bin/env python3
"""
Générateur de configuration MoveIt pour le robot Lynx SES900
Basé sur l'analyse de l'espace de travail
"""

import json
import os
import xml.etree.ElementTree as ET

class LynxMoveItConfigGenerator:
    def __init__(self):
        self.lynx_analysis = self.load_analysis()
        self.moveit_config = {}
    
    def load_analysis(self):
        """Charger les données d'analyse du Lynx"""
        try:
            with open("lynx_workspace_complete.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Fichier d'analyse non trouvé. Exécutez d'abord l'analyse complète.")
            return None
    
    def generate_joint_limits_config(self):
        """Générer la configuration des limites de joints pour MoveIt"""
        print("\n=== CONFIGURATION DES LIMITES DE JOINTS ===")
        
        if not self.lynx_analysis:
            return {}
        
        joint_limits = self.lynx_analysis["robot_info"]["joint_limits"]
        
        moveit_joint_limits = {}
        for joint_name, limits in joint_limits.items():
            moveit_joint_limits[joint_name] = {
                "has_velocity_limits": True,
                "max_velocity": limits["velocity"],
                "has_acceleration_limits": True,
                "max_acceleration": limits["velocity"] * 2,  # Estimation
                "has_jerk_limits": False,
                "has_effort_limits": True,
                "max_effort": limits["effort"]
            }
            
            print(f"{joint_name}:")
            print(f"  Vitesse max: {limits['velocity']} rad/s")
            print(f"  Effort max: {limits['effort']} N·m")
            print(f"  Limites: [{limits['lower']:.2f}, {limits['upper']:.2f}] rad")
        
        return moveit_joint_limits
    
    def generate_planning_config(self):
        """Générer la configuration de planification"""
        print("\n=== CONFIGURATION DE PLANIFICATION ===")
        
        if not self.lynx_analysis:
            return {}
        
        analysis = self.lynx_analysis["analysis"]
        max_reach = analysis["reach"]["max_distance"]
        
        planning_config = {
            "planner_configs": {
                "RRTConnect": {
                    "type": "geometric::RRTConnect",
                    "range": min(0.1, max_reach * 0.1),  # 10% de la portée max
                    "longest_valid_segment_fraction": 0.01
                },
                "RRT": {
                    "type": "geometric::RRT",
                    "range": min(0.1, max_reach * 0.1),
                    "goal_bias": 0.05
                },
                "PRM": {
                    "type": "geometric::PRM",
                    "max_nearest_neighbors": 10
                }
            },
            "planning_time": 5.0,
            "planning_attempts": 10,
            "max_velocity_scaling_factor": 0.1,
            "max_acceleration_scaling_factor": 0.1,
            "workspace_bounds": {
                "min_corner": [
                    analysis["bounds"]["x"]["min"],
                    analysis["bounds"]["y"]["min"],
                    analysis["bounds"]["z"]["min"]
                ],
                "max_corner": [
                    analysis["bounds"]["x"]["max"],
                    analysis["bounds"]["y"]["max"],
                    analysis["bounds"]["z"]["max"]
                ]
            }
        }
        
        print(f"Portée de planification: {planning_config['planner_configs']['RRTConnect']['range']:.3f} m")
        print(f"Limites de l'espace de travail:")
        print(f"  Min: {planning_config['workspace_bounds']['min_corner']}")
        print(f"  Max: {planning_config['workspace_bounds']['max_corner']}")
        
        return planning_config
    
    def generate_kinematics_config(self):
        """Générer la configuration cinématique"""
        print("\n=== CONFIGURATION CINÉMATIQUE ===")
        
        kinematics_config = {
            "manipulator": {
                "kinematics_solver": "kdl_kinematics_plugin/KDLKinematicsPlugin",
                "kinematics_solver_search_resolution": 0.005,
                "kinematics_solver_timeout": 0.05,
                "kinematics_solver_attempts": 3,
                "position_only_ik": False,
                "solve_type": "Speed"
            }
        }
        
        print("Solveur cinématique: KDL")
        print("Résolution de recherche: 0.005")
        print("Timeout: 0.05 s")
        
        return kinematics_config
    
    def generate_controllers_config(self):
        """Générer la configuration des contrôleurs"""
        print("\n=== CONFIGURATION DES CONTRÔLEURS ===")
        
        if not self.lynx_analysis:
            return {}
        
        joints = self.lynx_analysis["robot_info"]["joints"]
        
        controllers_config = {
            "controller_list": [
                {
                    "name": "lynx_arm_controller",
                    "action_ns": "follow_joint_trajectory",
                    "type": "FollowJointTrajectory",
                    "default": True,
                    "joints": joints
                }
            ]
        }
        
        print(f"Contrôleur principal: lynx_arm_controller")
        print(f"Joints contrôlés: {joints}")
        
        return controllers_config
    
    def generate_srdf_content(self):
        """Générer le contenu SRDF de base"""
        print("\n=== CONFIGURATION SRDF ===")
        
        srdf_content = """<?xml version="1.0" ?>
<robot name="lynx_ses900">
    <!--GROUPS: Representation of a set of joints and links. This can be useful for specifying DOF to plan for, defining arms, end effectors, etc-->
    <!--LINKS: When a link is specified, the parent joint of that link (if it exists) is automatically included-->
    <!--JOINTS: When a joint is specified, the child link of that joint (which will always exist) is automatically included-->
    <!--CHAINS: When a chain is specified, all the links along the chain (including endpoints) are included in the group. Additionally, all the joints that are parents to included links are also included. This means that joints along the chain and the parent joint of the base link are included in the group-->
    <!--SUBGROUPS: Groups can also be formed by referencing to already defined group names-->
    
    <group name="manipulator">
        <chain base_link="base_link" tip_link="tool_link" />
    </group>
    
    <group name="end_effector">
        <link name="tool_link" />
    </group>
    
    <!--GROUP STATES: Purpose: Define a named state for a particular group, in terms of joint values. This is useful to define a default position, or "parking" positions.-->
    <group_state name="home" group="manipulator">
        <joint name="joint_1" value="0" />
        <joint name="joint_2" value="0" />
        <joint name="joint_3" value="0" />
        <joint name="joint_4" value="0" />
        <joint name="joint_5" value="0" />
        <joint name="joint_6" value="0" />
    </group_state>
    
    <group_state name="ready" group="manipulator">
        <joint name="joint_1" value="0" />
        <joint name="joint_2" value="-1.57" />
        <joint name="joint_3" value="1.57" />
        <joint name="joint_4" value="0" />
        <joint name="joint_5" value="0" />
        <joint name="joint_6" value="0" />
    </group_state>
    
    <!--VIRTUAL JOINT: Purpose: this element defines a virtual joint between a robot link and an external frame of reference (considered fixed)-->
    <virtual_joint name="fixed_base" type="fixed" parent_frame="world" child_link="base_link" />
    
    <!--DISABLE COLLISIONS: By default it is assumed that any link of the robot could potentially come into collision with any other link in the robot. This tag disables collision checking between a specified pair of links. -->
    <disable_collisions link1="base_link" link2="shoulder_link" reason="Adjacent" />
    <disable_collisions link1="shoulder_link" link2="upper_arm_link" reason="Adjacent" />
    <disable_collisions link1="upper_arm_link" link2="forearm_link" reason="Adjacent" />
    <disable_collisions link1="forearm_link" link2="wrist_link" reason="Adjacent" />
    <disable_collisions link1="wrist_link" link2="hand_link" reason="Adjacent" />
    <disable_collisions link1="hand_link" link2="tool_link" reason="Adjacent" />
    
</robot>"""
        
        print("SRDF généré avec groupes: manipulator, end_effector")
        print("États prédéfinis: home, ready")
        
        return srdf_content
    
    def save_moveit_configs(self):
        """Sauvegarder toutes les configurations MoveIt"""
        print("\n=== SAUVEGARDE DES CONFIGURATIONS MOVEIT ===")
        
        # Créer le répertoire de configuration
        config_dir = "lynx_moveit_config"
        os.makedirs(config_dir, exist_ok=True)
        
        configs = {
            "joint_limits.yaml": self.generate_joint_limits_config(),
            "ompl_planning.yaml": self.generate_planning_config(),
            "kinematics.yaml": self.generate_kinematics_config(),
            "controllers.yaml": self.generate_controllers_config()
        }
        
        # Sauvegarder les fichiers YAML (simulés en JSON pour simplicité)
        for filename, config in configs.items():
            filepath = os.path.join(config_dir, filename.replace('.yaml', '.json'))
            try:
                with open(filepath, 'w') as f:
                    json.dump(config, f, indent=2)
                print(f"✅ Sauvegardé: {filepath}")
            except Exception as e:
                print(f"❌ Erreur sauvegarde {filepath}: {e}")
        
        # Sauvegarder le SRDF
        srdf_content = self.generate_srdf_content()
        srdf_path = os.path.join(config_dir, "lynx_ses900.srdf")
        try:
            with open(srdf_path, 'w') as f:
                f.write(srdf_content)
            print(f"✅ Sauvegardé: {srdf_path}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde SRDF: {e}")
        
        # Générer un fichier de documentation
        self.generate_usage_documentation(config_dir)
    
    def generate_usage_documentation(self, config_dir):
        """Générer la documentation d'usage"""
        doc_content = """# Configuration MoveIt pour Lynx SES900

## Fichiers générés

1. **joint_limits.json** - Limites des joints et vitesses
2. **ompl_planning.json** - Configuration des planificateurs OMPL
3. **kinematics.json** - Configuration du solveur cinématique
4. **controllers.json** - Configuration des contrôleurs
5. **lynx_ses900.srdf** - Fichier SRDF avec groupes et états

## Utilisation

### Lancement avec MoveIt

```bash
roslaunch lynx_moveit_config move_group.launch
```

### États prédéfinis

- **home**: Position neutre (tous joints à 0)
- **ready**: Position prête pour manipulation

### Groupes de planification

- **manipulator**: Chaîne cinématique complète
- **end_effector**: Effecteur terminal uniquement

### Recommandations

1. **Zone de travail optimale**: < 0.69 m du centre
2. **Zone de travail sûre**: < 0.83 m du centre
3. **Portée maximale**: 0.98 m

### Paramètres de sécurité

- Vitesse maximale réduite à 10% par défaut
- Accélération limitée à 10% par défaut
- Planification avec timeout de 5 secondes

## Calibration requise

Avant utilisation, effectuer:
1. Calibration des joints
2. Vérification des limites
3. Test de l'espace de travail
4. Validation des collisions

## Support

Basé sur l'analyse de l'espace de travail du Lynx SES900.
Voir les fichiers d'analyse pour plus de détails.
"""
        
        doc_path = os.path.join(config_dir, "README.md")
        try:
            with open(doc_path, 'w') as f:
                f.write(doc_content)
            print(f"✅ Documentation sauvegardée: {doc_path}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde documentation: {e}")
    
    def run_config_generation(self):
        """Exécuter la génération complète de configuration"""
        print("🔧 GÉNÉRATION DE CONFIGURATION MOVEIT - LYNX SES900")
        print("=" * 60)
        
        if not self.lynx_analysis:
            print("❌ Impossible de générer la configuration sans analyse.")
            return
        
        # Générer toutes les configurations
        self.save_moveit_configs()
        
        print(f"\n🎉 Configuration MoveIt générée!")
        print(f"📁 Fichiers disponibles dans le dossier: lynx_moveit_config/")
        print(f"📚 Consultez README.md pour les instructions d'utilisation")

def main():
    generator = LynxMoveItConfigGenerator()
    generator.run_config_generation()

if __name__ == "__main__":
    main()
