#!/usr/bin/env python3
"""
Analyseur simple de l'espace de travail du robot Lynx SES900
Analyse basée uniquement sur l'URDF sans dépendances ROS
"""

import xml.etree.ElementTree as ET
import json
import os
import sys

class SimpleLynxAnalyzer:
    def __init__(self, urdf_path=None):
        self.urdf_path = urdf_path or "real_robot/robot_models/URDF_description/urdf/lynx_ses900_optimized.urdf"
        self.robot_data = self.parse_urdf()
    
    def parse_urdf(self):
        """Analyser le fichier URDF du Lynx SES900"""
        print("=== ANALYSE URDF LYNX SES900 ===")
        print(f"Fichier: {self.urdf_path}")
        
        if not os.path.exists(self.urdf_path):
            print(f"❌ Fichier URDF non trouvé: {self.urdf_path}")
            return self.get_default_data()
        
        try:
            tree = ET.parse(self.urdf_path)
            root = tree.getroot()
            
            robot_data = {
                'name': root.get('name', 'lynx_ses900'),
                'links': {},
                'joints': {},
                'kinematic_chain': [],
                'workspace_specs': {}
            }
            
            # Analyser les liens
            print("\n--- LIENS ---")
            for link in root.findall('link'):
                link_name = link.get('name')
                link_data = {'name': link_name, 'mass': 0.0, 'inertia': None}
                
                inertial = link.find('inertial')
                if inertial is not None:
                    mass_elem = inertial.find('mass')
                    if mass_elem is not None:
                        link_data['mass'] = float(mass_elem.get('value'))
                    
                    origin = inertial.find('origin')
                    if origin is not None:
                        xyz = [float(x) for x in origin.get('xyz', '0 0 0').split()]
                        link_data['center_of_mass'] = xyz
                
                robot_data['links'][link_name] = link_data
                print(f"  {link_name}: masse = {link_data['mass']} kg")
            
            # Analyser les joints
            print("\n--- JOINTS ---")
            for joint in root.findall('joint'):
                joint_name = joint.get('name')
                joint_type = joint.get('type')
                
                if joint_type in ['revolute', 'continuous']:
                    joint_data = {
                        'name': joint_name,
                        'type': joint_type,
                        'parent': joint.find('parent').get('link'),
                        'child': joint.find('child').get('link'),
                        'limits': {},
                        'axis': [0, 0, 1],
                        'origin': {'xyz': [0, 0, 0], 'rpy': [0, 0, 0]}
                    }
                    
                    # Limites
                    limit = joint.find('limit')
                    if limit is not None:
                        joint_data['limits'] = {
                            'lower': float(limit.get('lower', '-3.1416')),
                            'upper': float(limit.get('upper', '3.1416')),
                            'effort': float(limit.get('effort', '50')),
                            'velocity': float(limit.get('velocity', '1.5'))
                        }
                    
                    # Axe de rotation
                    axis = joint.find('axis')
                    if axis is not None:
                        joint_data['axis'] = [float(x) for x in axis.get('xyz', '0 0 1').split()]
                    
                    # Transformation
                    origin = joint.find('origin')
                    if origin is not None:
                        joint_data['origin']['xyz'] = [float(x) for x in origin.get('xyz', '0 0 0').split()]
                        joint_data['origin']['rpy'] = [float(x) for x in origin.get('rpy', '0 0 0').split()]
                    
                    robot_data['joints'][joint_name] = joint_data
                    
                    # Affichage
                    limits = joint_data['limits']
                    lower_deg = limits.get('lower', 0) * 180 / 3.14159
                    upper_deg = limits.get('upper', 0) * 180 / 3.14159
                    print(f"  {joint_name}: [{lower_deg:.1f}°, {upper_deg:.1f}°] - Effort: {limits.get('effort', 0)} N·m")
            
            # Construire la chaîne cinématique
            robot_data['kinematic_chain'] = self.build_kinematic_chain(robot_data)
            
            # Calculer les spécifications de l'espace de travail
            robot_data['workspace_specs'] = self.calculate_workspace_specs(robot_data)
            
            print("✅ URDF analysé avec succès")
            return robot_data
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse URDF: {e}")
            return self.get_default_data()
    
    def build_kinematic_chain(self, robot_data):
        """Construire la chaîne cinématique depuis la base jusqu'à l'effecteur"""
        chain = []
        
        # Ordre des joints pour le Lynx SES900
        joint_order = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']
        
        for joint_name in joint_order:
            if joint_name in robot_data['joints']:
                joint = robot_data['joints'][joint_name]
                chain.append({
                    'joint_name': joint_name,
                    'parent_link': joint['parent'],
                    'child_link': joint['child'],
                    'translation': joint['origin']['xyz'],
                    'rotation': joint['origin']['rpy'],
                    'axis': joint['axis'],
                    'limits': joint['limits']
                })
        
        return chain
    
    def calculate_workspace_specs(self, robot_data):
        """Calculer les spécifications approximatives de l'espace de travail"""
        specs = {
            'num_joints': len(robot_data['joints']),
            'total_mass': sum(link['mass'] for link in robot_data['links'].values()),
            'link_lengths': [],
            'max_reach': 0.0,
            'joint_ranges': {}
        }
        
        # Calculer les longueurs approximatives des liens
        total_reach = 0.0
        for segment in robot_data['kinematic_chain']:
            translation = segment['translation']
            length = (translation[0]**2 + translation[1]**2 + translation[2]**2)**0.5
            specs['link_lengths'].append(length)
            total_reach += length
            
            # Plage de mouvement des joints
            limits = segment['limits']
            joint_range = limits.get('upper', 0) - limits.get('lower', 0)
            specs['joint_ranges'][segment['joint_name']] = {
                'range_rad': joint_range,
                'range_deg': joint_range * 180 / 3.14159
            }
        
        specs['max_reach'] = total_reach
        specs['estimated_workspace_radius'] = total_reach * 0.8  # Estimation conservative
        
        return specs
    
    def get_default_data(self):
        """Données par défaut si l'URDF n'est pas accessible"""
        return {
            'name': 'lynx_ses900',
            'links': {
                'base_link': {'mass': 1.5},
                'shoulder_link': {'mass': 0.8},
                'upper_arm_link': {'mass': 0.6},
                'forearm_link': {'mass': 0.4},
                'wrist_link': {'mass': 0.3},
                'hand_link': {'mass': 0.2},
                'tool_link': {'mass': 0.1}
            },
            'workspace_specs': {
                'num_joints': 6,
                'total_mass': 3.9,
                'max_reach': 0.6,
                'estimated_workspace_radius': 0.5
            }
        }
    
    def display_analysis(self):
        """Afficher l'analyse complète"""
        print(f"\n{'='*60}")
        print(f"RAPPORT D'ANALYSE - ROBOT {self.robot_data['name'].upper()}")
        print(f"{'='*60}")
        
        # Informations générales
        print(f"\n📊 CARACTÉRISTIQUES GÉNÉRALES")
        print(f"   Nombre de joints: {self.robot_data['workspace_specs']['num_joints']}")
        print(f"   Nombre de liens: {len(self.robot_data['links'])}")
        print(f"   Masse totale: {self.robot_data['workspace_specs']['total_mass']:.2f} kg")
        
        # Spécifications de l'espace de travail
        if 'workspace_specs' in self.robot_data:
            specs = self.robot_data['workspace_specs']
            print(f"\n🎯 ESPACE DE TRAVAIL")
            print(f"   Portée maximale estimée: {specs.get('max_reach', 0):.3f} m")
            print(f"   Rayon d'espace de travail: {specs.get('estimated_workspace_radius', 0):.3f} m")
        
        # Plages des joints
        if 'joint_ranges' in self.robot_data.get('workspace_specs', {}):
            print(f"\n🔄 PLAGES DE MOUVEMENT DES JOINTS")
            for joint_name, range_data in self.robot_data['workspace_specs']['joint_ranges'].items():
                print(f"   {joint_name}: ±{range_data['range_deg']/2:.1f}° ({range_data['range_rad']:.2f} rad)")
        
        # Chaîne cinématique
        if self.robot_data.get('kinematic_chain'):
            print(f"\n🔗 CHAÎNE CINÉMATIQUE")
            for i, segment in enumerate(self.robot_data['kinematic_chain']):
                trans = segment['translation']
                print(f"   {i+1}. {segment['joint_name']}: {segment['parent_link']} → {segment['child_link']}")
                print(f"      Translation: [{trans[0]:.3f}, {trans[1]:.3f}, {trans[2]:.3f}] m")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS")
        max_reach = self.robot_data['workspace_specs'].get('max_reach', 0)
        if max_reach > 0:
            print(f"   • Zone de travail optimale: rayon < {max_reach*0.7:.2f} m")
            print(f"   • Zone accessible: rayon < {max_reach*0.9:.2f} m")
            print(f"   • Éviter les singularités près des limites articulaires")
        
        print(f"   • Surveiller les couples articulaires lors de charges importantes")
        print(f"   • Calibration recommandée avant utilisation")
    
    def save_report(self, filename="lynx_analysis_report.json"):
        """Sauvegarder le rapport d'analyse"""
        report = {
            'robot_model': self.robot_data['name'],
            'analysis_type': 'URDF_geometric_analysis',
            'robot_data': self.robot_data,
            'recommendations': {
                'optimal_work_radius': self.robot_data['workspace_specs'].get('max_reach', 0) * 0.7,
                'max_safe_radius': self.robot_data['workspace_specs'].get('max_reach', 0) * 0.9,
                'calibration_required': True,
                'collision_avoidance': True
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Rapport sauvegardé: {filename}")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
    
    def compare_with_ur5(self):
        """Comparaison avec l'UR5 pour référence"""
        ur5_specs = {
            'max_reach': 0.85,
            'payload': 5.0,
            'mass': 18.4,
            'joints': 6
        }
        
        lynx_specs = self.robot_data['workspace_specs']
        
        print(f"\n⚖️  COMPARAISON LYNX vs UR5")
        print(f"   Portée max - Lynx: {lynx_specs.get('max_reach', 0):.2f}m | UR5: {ur5_specs['max_reach']:.2f}m")
        print(f"   Masse - Lynx: {lynx_specs.get('total_mass', 0):.1f}kg | UR5: {ur5_specs['mass']:.1f}kg")
        print(f"   Joints - Lynx: {lynx_specs.get('num_joints', 0)} | UR5: {ur5_specs['joints']}")
        
        if lynx_specs.get('max_reach', 0) < ur5_specs['max_reach']:
            print(f"   🎯 Lynx: Robot plus compact, idéal pour espaces restreints")
        if lynx_specs.get('total_mass', 0) < ur5_specs['mass']:
            print(f"   ⚡ Lynx: Plus léger, installation plus flexible")

def main():
    print("🤖 ANALYSEUR LYNX SES900")
    print("========================")
    
    # Chemin vers l'URDF
    if len(sys.argv) > 1:
        urdf_path = sys.argv[1]
    else:
        urdf_path = None
    
    # Créer l'analyseur
    analyzer = SimpleLynxAnalyzer(urdf_path)
    
    # Exécuter l'analyse
    analyzer.display_analysis()
    analyzer.compare_with_ur5()
    analyzer.save_report()
    
    print(f"\n🎉 Analyse terminée!")
    print(f"📄 Rapport détaillé sauvegardé dans lynx_analysis_report.json")

if __name__ == "__main__":
    main()
