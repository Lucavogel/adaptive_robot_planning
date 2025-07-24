#!/usr/bin/env python3
"""
Script pour afficher le résumé de l'organisation du workspace Lynx
"""

import os

def display_workspace_summary():
    """Afficher le résumé de l'organisation du workspace"""
    
    # Déterminer si on est dans le dossier lynx_workspace ou à l'extérieur
    if os.path.basename(os.getcwd()) == "lynx_workspace":
        workspace_dir = "."
        print("🗂️  ORGANISATION DU WORKSPACE LYNX SES900")
        print("=" * 60)
        print(f"📁 Dossier principal: lynx_workspace/ (répertoire courant)")
    else:
        workspace_dir = "lynx_workspace"
        print("🗂️  ORGANISATION DU WORKSPACE LYNX SES900")
        print("=" * 60)
        print(f"📁 Dossier principal: {workspace_dir}/")
    
    # Compter les fichiers par catégorie
    file_categories = {
        "📊 Rapports d'analyse": [
            "lynx_analysis_report.json",
            "lynx_workspace_complete.json", 
            "lynx_synthesis_report.json",
            "LYNX_FINAL_ANALYSIS_REPORT.json",
            "LYNX_ANALYSIS_SUMMARY.md"
        ],
        "📈 Visualisations": [
            "lynx_workspace_complete.png",
            "lynx_workspace_complete_analysis.png"
        ],
        "🐍 Scripts d'analyse": [
            "simple_lynx_analyzer.py",
            "lynx_workspace_complete.py",
            "lynx_synthesis.py", 
            "lynx_moveit_config_generator.py",
            "lynx_workspace_analyzer.py",
            "lynx_workspace.py"
        ],
        "🔧 Configuration MoveIt": [
            "lynx_moveit_config/"
        ],
        "📖 Documentation": [
            "README.md"
        ]
    }
    
    total_files = 0
    total_size = 0
    
    print(f"\n📋 CONTENU DU WORKSPACE")
    print("-" * 40)
    
    for category, files in file_categories.items():
        print(f"\n{category}")
        category_count = 0
        category_size = 0
        
        for file in files:
            file_path = os.path.join(workspace_dir, file)
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    size_str = format_file_size(size)
                    print(f"  ✅ {file} ({size_str})")
                    category_count += 1
                    category_size += size
                    total_size += size
                elif os.path.isdir(file_path):
                    dir_files = count_files_in_dir(file_path)
                    dir_size = get_dir_size(file_path)
                    size_str = format_file_size(dir_size)
                    print(f"  ✅ {file} ({dir_files} fichiers, {size_str})")
                    category_count += dir_files
                    category_size += dir_size
                    total_size += dir_size
            else:
                print(f"  ❌ {file}")
        
        if category_count > 0:
            category_size_str = format_file_size(category_size)
            print(f"    📊 {category_count} éléments, {category_size_str}")
        
        total_files += category_count
    
    # Résumé final
    total_size_str = format_file_size(total_size)
    print(f"\n🎯 RÉSUMÉ FINAL")
    print("-" * 40)
    print(f"📁 Dossier: {workspace_dir}/")
    print(f"📄 Total fichiers: {total_files}")
    print(f"💾 Taille totale: {total_size_str}")
    
    # Vérifier l'intégrité
    print(f"\n✅ VÉRIFICATION D'INTÉGRITÉ")
    print("-" * 40)
    
    essential_files = [
        "lynx_workspace_complete.json",
        "LYNX_FINAL_ANALYSIS_REPORT.json", 
        "LYNX_ANALYSIS_SUMMARY.md",
        "lynx_moveit_config/lynx_ses900.srdf",
        "README.md"
    ]
    
    all_present = True
    for file in essential_files:
        file_path = os.path.join(workspace_dir, file)
        if os.path.exists(file_path):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MANQUANT")
            all_present = False
    
    if all_present:
        print(f"\n🎉 WORKSPACE COMPLET ET PRÊT À L'USAGE!")
        if workspace_dir == ".":
            print(f"📖 Consultez README.md pour commencer")
        else:
            print(f"📖 Consultez {workspace_dir}/README.md pour commencer")
    else:
        print(f"\n⚠️  Certains fichiers essentiels sont manquants")
    
    # Instructions d'utilisation
    print(f"\n🚀 UTILISATION RAPIDE")
    print("-" * 40)
    if workspace_dir == ".":
        print(f"python3 simple_lynx_analyzer.py        # Analyse rapide")
        print(f"python3 lynx_workspace_complete.py     # Analyse complète") 
        print(f"python3 lynx_synthesis.py              # Synthèse")
        print(f"python3 lynx_moveit_config_generator.py # Config MoveIt")
    else:
        print(f"cd {workspace_dir}")
        print(f"python3 simple_lynx_analyzer.py        # Analyse rapide")
        print(f"python3 lynx_workspace_complete.py     # Analyse complète") 
        print(f"python3 lynx_synthesis.py              # Synthèse")
        print(f"python3 lynx_moveit_config_generator.py # Config MoveIt")

def format_file_size(size_bytes):
    """Formater la taille de fichier en unités lisibles"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

def count_files_in_dir(directory):
    """Compter le nombre de fichiers dans un répertoire"""
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count

def get_dir_size(directory):
    """Calculer la taille totale d'un répertoire"""
    total_size = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
    return total_size

if __name__ == "__main__":
    display_workspace_summary()
