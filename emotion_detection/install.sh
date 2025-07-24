#!/bin/bash

echo "Installation des dépendances pour la détection d'émotions..."

# Vérifier si pip est installé
if ! command -v pip &> /dev/null; then
    echo "pip n'est pas installé. Installation de pip..."
    sudo apt update
    sudo apt install python3-pip -y
fi

# Installer les dépendances
echo "Installation des packages Python..."
pip install -r requirements.txt

echo "Installation terminée!"
echo ""
echo "Pour lancer la détection d'émotions, exécutez:"
echo "python3 emotion_detector.py"
