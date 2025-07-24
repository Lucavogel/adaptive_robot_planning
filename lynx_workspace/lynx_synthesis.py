#!/usr/bin/env python3
"""
Synthèse d'analyse de l'espace de travail du robot Lynx SES900
"""

import json
import os

class LynxWorkspaceSynthesis:
    def __init__(self):
        self.reports = {}
        self.load_analysis_files()
    
    def load_analysis_files(self):
        """Charger tous les fichiers d'analyse disponibles"""
        analysis_files = [
            ("simple_analysis", "lynx_analysis_report.json"),
            ("complete_analysis", "lynx_workspace_complete.json")
        ]
        
        for analysis_type, filename in analysis_files:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r') as f:
                        self.reports[analysis_type] = json.load(f)
                    print(f"✅ Chargé: {filename}")
                except Exception as e:
                    print(f"❌ Erreur chargement {filename}: {e}")
            else:
                print(f"⚠️  Fichier non trouvé: {filename}")
    
    def generate_synthesis_report(self):
        """Générer un rapport de synthèse complet"""
        print("\n" + "="*80)
        print("SYNTHÈSE D'ANALYSE - ROBOT LYNX SES900")
        print("="*80)
        
        # Informations générales du robot
        self.display_robot_overview()
        
        # Analyse géométrique
        self.display_geometric_analysis()
        
        # Analyse de l'espace de travail
        self.display_workspace_analysis()
        
        # Comparaisons et recommandations
        self.display_recommendations()
        
        # Sauvegarder le rapport de synthèse
        self.save_synthesis_report()
    
    def display_robot_overview(self):
        """Afficher aperçu général du robot"""
        print(f"\n📋 APERÇU GÉNÉRAL DU ROBOT")
        print("-" * 40)
        
        if "simple_analysis" in self.reports:
            robot_data = self.reports["simple_analysis"]["robot_data"]
            workspace_specs = robot_data.get("workspace_specs", {})
            
            print(f"Nom du robot: {robot_data['name']}")
            print(f"Nombre de joints: {workspace_specs.get('num_joints', 'N/A')}")
            print(f"Nombre de liens: {len(robot_data.get('links', {}))}")
            print(f"Masse totale: {workspace_specs.get('total_mass', 'N/A')} kg")
            
            # Capacités des joints
            print(f"\n🔧 CAPACITÉS DES JOINTS")
            if "joints" in robot_data:
                for joint_name, joint_data in robot_data["joints"].items():
                    if "limits" in joint_data:
                        effort = joint_data["limits"].get("effort", 0)
                        velocity = joint_data["limits"].get("velocity", 0)
                        print(f"  {joint_name}: {effort} N·m, {velocity} rad/s")
    
    def display_geometric_analysis(self):
        """Afficher analyse géométrique"""
        print(f"\n📏 ANALYSE GÉOMÉTRIQUE")
        print("-" * 40)
        
        if "simple_analysis" in self.reports:
            robot_data = self.reports["simple_analysis"]["robot_data"]
            workspace_specs = robot_data.get("workspace_specs", {})
            
            max_reach = workspace_specs.get("max_reach", 0)
            print(f"Portée maximale théorique: {max_reach:.3f} m")
            
            if "link_lengths" in workspace_specs:
                link_lengths = workspace_specs["link_lengths"]
                print(f"Longueurs des segments:")
                for i, length in enumerate(link_lengths):
                    print(f"  Segment {i+1}: {length:.3f} m")
    
    def display_workspace_analysis(self):
        """Afficher analyse de l'espace de travail"""
        print(f"\n🎯 ANALYSE DE L'ESPACE DE TRAVAIL")
        print("-" * 40)
        
        if "complete_analysis" in self.reports:
            analysis = self.reports["complete_analysis"]["analysis"]
            
            print(f"Échantillons analysés: {analysis['num_points']:,}")
            
            # Limites spatiales
            bounds = analysis["bounds"]
            print(f"\nLimites spatiales:")
            print(f"  X: [{bounds['x']['min']:.3f}, {bounds['x']['max']:.3f}] m (portée: {bounds['x']['range']:.3f} m)")
            print(f"  Y: [{bounds['y']['min']:.3f}, {bounds['y']['max']:.3f}] m (portée: {bounds['y']['range']:.3f} m)")
            print(f"  Z: [{bounds['z']['min']:.3f}, {bounds['z']['max']:.3f}] m (portée: {bounds['z']['range']:.3f} m)")
            
            # Portées
            reach = analysis["reach"]
            print(f"\nPortées mesurées:")
            print(f"  Distance maximale: {reach['max_distance']:.3f} m")
            print(f"  Distance minimale: {reach['min_distance']:.3f} m")
            print(f"  Portée XY maximale: {reach['max_xy_distance']:.3f} m")
            
            # Volume
            volume = analysis["volume"]
            print(f"\nVolume de travail:")
            print(f"  Boîte englobante: {volume['bounding_box']:.3f} m³")
    
    def display_recommendations(self):
        """Afficher recommandations et comparaisons"""
        print(f"\n💡 RECOMMANDATIONS D'UTILISATION")
        print("-" * 40)
        
        if "complete_analysis" in self.reports:
            analysis = self.reports["complete_analysis"]["analysis"]
            max_distance = analysis["reach"]["max_distance"]
            
            print(f"Zone de travail optimale: < {max_distance * 0.7:.2f} m du centre")
            print(f"Zone de travail sûre: < {max_distance * 0.85:.2f} m du centre")
            print(f"Zone d'atteinte maximale: < {max_distance:.2f} m du centre")
            
            print(f"\n⚠️  PRÉCAUTIONS:")
            print(f"  • Éviter les singularités aux limites des joints")
            print(f"  • Surveiller les couples lors de charges importantes")
            print(f"  • Calibration requise avant utilisation")
            print(f"  • Vérifier les collisions dans l'environnement de travail")
        
        print(f"\n⚖️  COMPARAISON AVEC D'AUTRES ROBOTS")
        print("-" * 40)
        
        # Comparaisons avec robots standards
        robots_comparison = {
            "UR5": {"reach": 0.85, "payload": 5.0, "mass": 18.4, "precision": 0.1},
            "UR3": {"reach": 0.5, "payload": 3.0, "mass": 11.0, "precision": 0.1},
            "KUKA iiwa 7": {"reach": 0.8, "payload": 7.0, "mass": 22.0, "precision": 0.1}
        }
        
        if "complete_analysis" in self.reports:
            lynx_reach = self.reports["complete_analysis"]["analysis"]["reach"]["max_distance"]
            lynx_mass = 3.9  # De l'analyse précédente
            
            print(f"Lynx SES900:")
            print(f"  Portée: {lynx_reach:.2f} m")
            print(f"  Masse: {lynx_mass} kg")
            
            print(f"\nComparaison:")
            for robot_name, specs in robots_comparison.items():
                reach_diff = ((lynx_reach - specs["reach"]) / specs["reach"]) * 100
                mass_diff = ((lynx_mass - specs["mass"]) / specs["mass"]) * 100
                print(f"  vs {robot_name}:")
                print(f"    Portée: {reach_diff:+.1f}% ({specs['reach']} m)")
                print(f"    Masse: {mass_diff:+.1f}% ({specs['mass']} kg)")
            
            print(f"\n🎯 AVANTAGES DU LYNX SES900:")
            if lynx_reach > 0.8:
                print(f"  ✅ Excellente portée pour sa catégorie")
            if lynx_mass < 10:
                print(f"  ✅ Très léger - installation flexible")
            print(f"  ✅ 6 DOF - polyvalence complète")
            print(f"  ✅ Rapport portée/poids excellent")
    
    def save_synthesis_report(self):
        """Sauvegarder le rapport de synthèse"""
        synthesis_data = {
            "robot_model": "lynx_ses900",
            "synthesis_type": "complete_workspace_analysis",
            "summary": {},
            "recommendations": {},
            "comparisons": {}
        }
        
        # Résumé des analyses
        if "complete_analysis" in self.reports:
            analysis = self.reports["complete_analysis"]["analysis"]
            synthesis_data["summary"] = {
                "samples_analyzed": analysis["num_points"],
                "max_reach": analysis["reach"]["max_distance"],
                "workspace_volume": analysis["volume"]["bounding_box"],
                "spatial_bounds": analysis["bounds"]
            }
        
        # Recommandations
        if "complete_analysis" in self.reports:
            max_reach = self.reports["complete_analysis"]["analysis"]["reach"]["max_distance"]
            synthesis_data["recommendations"] = {
                "optimal_work_radius": max_reach * 0.7,
                "safe_work_radius": max_reach * 0.85,
                "max_reach": max_reach,
                "safety_considerations": [
                    "Éviter les singularités aux limites des joints",
                    "Surveiller les couples lors de charges importantes",
                    "Calibration requise avant utilisation",
                    "Vérifier les collisions dans l'environnement"
                ]
            }
        
        # Sauvegarder
        try:
            with open("lynx_synthesis_report.json", "w") as f:
                json.dump(synthesis_data, f, indent=2)
            print(f"\n✅ Rapport de synthèse sauvegardé: lynx_synthesis_report.json")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")

def main():
    print("🤖 SYNTHÈSE D'ANALYSE LYNX SES900")
    print("=================================")
    
    synthesizer = LynxWorkspaceSynthesis()
    synthesizer.generate_synthesis_report()
    
    print(f"\n🎉 Synthèse terminée!")
    print(f"📄 Tous les rapports disponibles dans le répertoire")

if __name__ == "__main__":
    main()
