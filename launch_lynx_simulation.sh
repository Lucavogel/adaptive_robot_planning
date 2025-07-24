#!/bin/bash

echo "🚀 Lancement système Lynx SES900 - Version simplifiée"

killall -9 roscore rosmaster python3 2>/dev/null || true
sleep 2

ROS_SETUP="source /opt/ros/noetic/setup.bash && source ~/catkin_ws/devel/setup.bash"

# Terminal 1: ROS Master
echo "📡 Démarrage ROS Master..."
gnome-terminal --title="🔧 ROS Master" --geometry=80x24+100+100 -- bash -c "
$ROS_SETUP
roscore
read -p 'Fermez-moi en dernier...'
"
sleep 5

# Terminal 2: MoveIt Lynx seulement
echo "🤖 Démarrage MoveIt Lynx..."
gnome-terminal --title="🤖 MoveIt Lynx" --geometry=80x24+500+100 -- bash -c "
$ROS_SETUP
roslaunch lynx_ses900_moveit_config demo.launch
read -p 'Appuyez sur Entrée pour fermer...'
"
sleep 8

# Terminal 3: Système perception complet
echo "🎯 Démarrage système perception..."
gnome-terminal --title="🎯 Caméra + ArUco + YOLO" --geometry=80x24+900+100 -- bash -c "
$ROS_SETUP
cd ~/catkin_ws/src/adaptive_robot_planning
roslaunch adaptive_robot_planning lynx_complete_system.launch
read -p 'Appuyez sur Entrée pour fermer...'
"
sleep 5

# Terminal 4: Application principale
echo "🎯 Lancement application principale..."
gnome-terminal --title="🎯 ASSISTANT LYNX" --geometry=100x30+300+400 -- bash -c "
$ROS_SETUP
cd ~/catkin_ws/src/adaptive_robot_planning
echo '🤖 Assistant Lynx SES900 prêt !'
python3 main.py
read -p 'Appuyez sur Entrée pour fermer...'
"

echo "✅ Système Lynx lancé avec 4 terminaux !"