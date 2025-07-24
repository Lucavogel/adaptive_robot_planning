#!/bin/bash

# Script de lancement pour la détection d'émotions
# Utilise l'environnement virtuel Python configuré

echo "Lancement de la détection d'émotions..."
echo "Appuyez sur 'q' pour quitter"
echo ""

# Aller dans le dossier emotion_detection
cd /home/soltani/catkin_ws/src/adaptive_robot_planning/emotion_detection

# Lancer le script avec l'environnement virtuel
./emotion_env/bin/python emotion_detector.py
