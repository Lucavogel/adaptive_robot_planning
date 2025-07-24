#!/bin/bash

echo "🛑 Arrêt complet du système Lynx SES900..."

# Arrêt en douceur
echo "🔄 Arrêt des processus ROS..."
pkill -f "roslaunch.*lynx"
pkill -f "roslaunch.*demo"
pkill -f "python3.*main.py"
pkill -f "python3.*aruco_detector"
pkill -f "python3.*camera_detection"
pkill -f "usb_cam_node"

sleep 3

# Arrêt du noyau ROS
echo "🔨 Arrêt de ROS Master..."
pkill -f "roscore"
pkill -f "rosmaster"

sleep 2

# Arrêt forcé si nécessaire
echo "⚡ Nettoyage final..."
killall -9 roscore rosmaster python3 2>/dev/null || true

# Fermer les terminaux
echo "🧹 Fermeture des terminaux..."
pkill -f "gnome-terminal.*ROS Master" 2>/dev/null || true
pkill -f "gnome-terminal.*MoveIt" 2>/dev/null || true
pkill -f "gnome-terminal.*Caméra" 2>/dev/null || true
pkill -f "gnome-terminal.*ASSISTANT" 2>/dev/null || true
pkill -f "gnome-terminal.*SYSTÈME" 2>/dev/null || true

echo "✅ Système complètement arrêté !"
echo "🧹 Tous les processus et terminaux fermés"