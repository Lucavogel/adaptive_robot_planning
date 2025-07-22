#!/bin/bash

echo "🚀 Starting MoveIt Full Trajectory Execution System"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "main_sim_full_trajectory.py" ]; then
    echo "❌ Error: Please run this script from the real_robot directory"
    exit 1
fi

# Clean old trajectory files
echo "🧹 Cleaning old trajectory files..."
rm -f /tmp/moveit_full_trajectory.json
rm -f /tmp/moveit_full_trajectory.json.tmp

# Start the MoveIt bridge in background
echo "🌉 Starting MoveIt Full Trajectory Bridge..."
python3 moveit_full_trajectory_bridge.py &
BRIDGE_PID=$!

# Wait a moment for bridge to initialize
sleep 2

# Start the simulation controller
echo "🤖 Starting Full Trajectory Simulation Controller..."
python3 main_sim_full_trajectory.py &
SIM_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Full Trajectory System..."
    kill $BRIDGE_PID 2>/dev/null
    kill $SIM_PID 2>/dev/null
    wait $BRIDGE_PID 2>/dev/null
    wait $SIM_PID 2>/dev/null
    echo "✅ Cleanup complete"
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

echo ""
echo "✅ Full Trajectory System is running!"
echo ""
echo "📋 Instructions:"
echo "1. Open MoveIt in another terminal"
echo "2. Plan a trajectory (multiple waypoints)"
echo "3. Watch the complete smooth execution here"
echo "4. Press Ctrl+C to stop everything"
echo ""
echo "🔗 Components running:"
echo "   - MoveIt Bridge (PID: $BRIDGE_PID)"
echo "   - Simulation Controller (PID: $SIM_PID)"
echo ""

# Wait for both processes
wait $BRIDGE_PID $SIM_PID
