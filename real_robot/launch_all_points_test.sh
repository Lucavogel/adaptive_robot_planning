#!/bin/bash
"""
Script de lancement pour TEST POINT-À-POINT COMPLET.
Lance le bridge qui capture TOUTE la trajectoire puis l'exécution point par point.
"""

echo "🎯 LANCEMENT DU SYSTÈME POINT-À-POINT COMPLET"
echo "============================================="
echo ""
echo "Ce système va:"
echo "  ✅ Capturer TOUTE la trajectoire MoveIt (début → fin)"
echo "  ✅ Attendre que la trajectoire soit COMPLÈTE"
echo "  ✅ Exécuter TOUS les waypoints un par un"
echo "  ✅ Attendre que chaque mouvement soit terminé"
echo "  📊 Test si l'interpolation est vraiment nécessaire"
echo ""

# Function to kill background processes
cleanup() {
    echo ""
    echo "🛑 Arrêt des processus..."
    kill $BRIDGE_PID 2>/dev/null
    kill $SIM_PID 2>/dev/null
    echo "✅ Nettoyage terminé"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if we're in the right directory
if [ ! -f "main_sim_all_points.py" ]; then
    echo "❌ Erreur: main_sim_all_points.py non trouvé"
    echo "📁 Assurez-vous d'être dans le répertoire real_robot/"
    exit 1
fi

# Source ROS2 environment
echo "🔧 Configuration de l'environnement ROS2..."
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
    echo "✅ ROS2 Humble configuré"
elif [ -f "/opt/ros/galactic/setup.bash" ]; then
    source /opt/ros/galactic/setup.bash
    echo "✅ ROS2 Galactic configuré"
else
    echo "⚠️  ROS2 non trouvé, continuons quand même..."
fi

# Source workspace if it exists
if [ -f "../UR_WS/install/setup.bash" ]; then
    source ../UR_WS/install/setup.bash
    echo "✅ Workspace UR configuré"
fi

echo ""
echo "🚀 LANCEMENT DES COMPOSANTS..."
echo ""

# Launch all points trajectory bridge in background
echo "1️⃣ Lancement du bridge TOUTE TRAJECTOIRE..."
python3 all_points_trajectory_bridge.py &
BRIDGE_PID=$!
echo "   📡 Bridge PID: $BRIDGE_PID"

# Wait a bit for bridge to start
sleep 2

# Launch all points simulation in background  
echo ""
echo "2️⃣ Lancement de la simulation POINT-À-POINT..."
python3 main_sim_all_points.py &
SIM_PID=$!
echo "   🤖 Simulation PID: $SIM_PID"

echo ""
echo "🎯 SYSTÈME POINT-À-POINT PRÊT!"
echo "==============================="
echo "📡 Bridge: PID $BRIDGE_PID"
echo "🤖 Simulation: PID $SIM_PID"
echo ""
echo "📋 INSTRUCTIONS:"
echo "   1. Ouvrez MoveIt dans un autre terminal"
echo "   2. Planifiez une trajectoire COMPLÈTE"
echo "   3. Le bridge va capturer TOUS les waypoints"
echo "   4. Le robot exécutera chaque waypoint individuellement"
echo "   5. Observez si le mouvement est fluide sans interpolation"
echo ""
echo "🔍 ANALYSE À OBSERVER:"
echo "   ✅ Le mouvement point-à-point est-il fluide?"
echo "   ✅ Y a-t-il des à-coups entre waypoints?"
echo "   ✅ Le timing entre waypoints est-il acceptable?"
echo "   ❓ L'interpolation est-elle vraiment nécessaire?"
echo ""
echo "📊 DONNÉES GÉNÉRÉES:"
echo "   📄 /tmp/moveit_all_points_trajectory.json"
echo ""
echo "⌨️  Appuyez sur CTRL+C pour arrêter"

# Wait for user interruption
wait
