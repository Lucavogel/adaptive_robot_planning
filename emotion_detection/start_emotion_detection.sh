#!/bin/bash

# Script principal pour la détection d'émotions
# Automatise l'installation et le lancement

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

echo "=== Système de Détection d'Émotions ==="
echo

# Vérifier si l'environnement virtuel existe
if [ ! -d "emotion_env" ]; then
    echo "🔧 Environnement virtuel non trouvé. Installation en cours..."
    
    # Vérifier si python3-venv est installé
    if ! dpkg -l | grep -q python3.8-venv; then
        echo "📦 Installation de python3-venv..."
        sudo apt update && sudo apt install python3.8-venv -y
    fi
    
    # Créer l'environnement virtuel
    echo "🐍 Création de l'environnement virtuel..."
    python3 -m venv emotion_env
    
    # Installer les dépendances
    echo "📋 Installation des dépendances..."
    ./emotion_env/bin/pip install --upgrade pip
    ./emotion_env/bin/pip install -r requirements.txt
    
    echo "✅ Installation terminée!"
    echo
fi

echo "🎯 Lancement de la détection d'émotions..."
echo "💡 Conseils d'utilisation :"
echo "   - Regardez directement la caméra"
echo "   - Assurez-vous d'avoir un bon éclairage"
echo "   - Appuyez sur 'q' pour quitter"
echo
echo "🚀 Démarrage dans 3 secondes..."
sleep 3

# Lancer la détection
./emotion_env/bin/python emotion_detector.py
