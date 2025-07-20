#!/bin/bash

# Script pour tester le robot Lynx SES900 avec le bridge hybrid
# Ce script démarre le bridge et lance les tests de mouvement

echo "🚀 Lynx SES900 Test Suite"
echo "=========================="
echo ""

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "real_robot/main_sim_ros_bridge_hybrid.py" ]; then
    echo "❌ Erreur: real_robot/main_sim_ros_bridge_hybrid.py non trouvé"
    echo "   Veuillez exécuter ce script depuis le répertoire racine du projet"
    exit 1
fi

# Fonction pour nettoyer en cas d'interruption
cleanup() {
    echo ""
    echo "🧹 Nettoyage en cours..."
    # Tuer tous les processus Python lancés par ce script
    pkill -f "main_sim_ros_bridge_hybrid.py" 2>/dev/null
    pkill -f "test_lynx_movements.py" 2>/dev/null
    echo "✅ Nettoyage terminé"
    exit 0
}

# Configurer le signal d'interruption
trap cleanup SIGINT SIGTERM

echo "1️⃣  Démarrage du bridge hybrid..."
echo "   Commande: python real_robot/main_sim_ros_bridge_hybrid.py"
echo ""

# Démarrer le bridge en arrière-plan
python real_robot/main_sim_ros_bridge_hybrid.py &
BRIDGE_PID=$!

# Attendre que le bridge soit prêt
echo "⏱️  Attente du démarrage du bridge (5 secondes)..."
sleep 5

# Vérifier que le bridge fonctionne
if ps -p $BRIDGE_PID > /dev/null; then
    echo "✅ Bridge démarré (PID: $BRIDGE_PID)"
else
    echo "❌ Erreur: Le bridge n'a pas pu démarrer"
    exit 1
fi

echo ""
echo "2️⃣  Lancement des tests de mouvement..."
echo "   Commande: python test_lynx_movements.py"
echo ""

# Lancer les tests
python test_lynx_movements.py

# Nettoyer
echo ""
echo "3️⃣  Arrêt du bridge..."
kill $BRIDGE_PID 2>/dev/null
wait $BRIDGE_PID 2>/dev/null

echo "✅ Test terminé avec succès!"
echo ""
echo "💡 Pour reproduire manuellement:"
echo "   Terminal 1: python real_robot/main_sim_ros_bridge_hybrid.py"
echo "   Terminal 2: python test_lynx_movements.py"
