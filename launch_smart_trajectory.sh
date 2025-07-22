#!/bin/bash
#
# Lanceur pour le système de trajectoire INTELLIGENT:
# 1. Bridge qui calcule TOUT à l'avance
# 2. Robot qui exécute ULTRA-RAPIDEMENT
#

echo "================================================"
echo "🧠 SYSTÈME DE TRAJECTOIRE INTELLIGENT"
echo "================================================"
echo "1. Bridge: Calcul intelligent + vitesses adaptatives"
echo "2. Robot: Exécution ultra-rapide pré-calculée"
echo "================================================"

# Aller dans le répertoire real_robot
cd "$(dirname "$0")/real_robot"
if [ ! -f "main_sim_smart_trajectory.py" ]; then
    echo "❌ Erreur: Fichiers non trouvés dans $(pwd)"
    echo "📁 Contenu du répertoire:"
    ls -la
    exit 1
fi

# Nettoyer les anciens fichiers de données
echo "🗑️ Nettoyage des anciens fichiers..."
rm -f /tmp/moveit_smart_trajectory.json
rm -f /tmp/moveit_full_trajectory.json

# Fonction pour nettoyer au signal CTRL-C
cleanup() {
    echo ""
    echo "🛑 CTRL-C détecté - Arrêt en cours..."
    
    # Tuer le bridge ROS
    if [ ! -z "$BRIDGE_PID" ]; then
        echo "🔌 Arrêt du bridge intelligent..."
        kill $BRIDGE_PID 2>/dev/null
        wait $BRIDGE_PID 2>/dev/null
    fi
    
    # Tuer le robot
    if [ ! -z "$ROBOT_PID" ]; then
        echo "🤖 Arrêt du robot..."
        kill $ROBOT_PID 2>/dev/null
        wait $ROBOT_PID 2>/dev/null
    fi
    
    echo "✅ Arrêt propre terminé"
    exit 0
}

# Configurer le signal handler
trap cleanup SIGINT SIGTERM

echo ""
echo "🔌 Démarrage du bridge intelligent..."
python3 smart_trajectory_processor.py &
BRIDGE_PID=$!

# Attendre que le bridge soit prêt
sleep 2

echo "🤖 Démarrage du robot executeur intelligent..."
python3 main_sim_smart_trajectory.py &
ROBOT_PID=$!

echo ""
echo "✅ SYSTÈME INTELLIGENT DÉMARRÉ!"
echo "------------------------------------------------"
echo "📋 Instructions:"
echo "   1. Ouvrez MoveIt dans un autre terminal"
echo "   2. Planifiez une trajectoire complète"
echo "   3. Le bridge calcule TOUT automatiquement"
echo "   4. Le robot exécute en ULTRA-RAPIDE"
echo "------------------------------------------------"
echo "📊 Surveillez les calculs et l'exécution..."
echo "🛑 CTRL-C pour arrêter proprement"
echo "================================================"

# Attendre que les processus se terminent
wait $BRIDGE_PID
wait $ROBOT_PID

echo "🏁 Système intelligent terminé."
