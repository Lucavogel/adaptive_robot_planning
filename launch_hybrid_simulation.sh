#!/bin/bash

# ==============================================================================
# LAUNCH HYBRID SIMULATION - MoveIt to PyBullet Synchronization (HYBRID VERSION)
# ==============================================================================
# This script launches the HYBRID version of the simulation system that buffers
# trajectory points for smoother execution.
#
# Prerequisites:
# - ROS2 environment sourced
# - MoveIt running (robot should be publishing on /joint_states)
# - PyBullet installed
#
# Usage: ./launch_hybrid_simulation.sh
# ==============================================================================

echo "🚀 Starting HYBRID MoveIt to PyBullet Synchronization System..."

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "moveit_to_pybullet_bridge.py" 2>/dev/null || true
pkill -f "main_sim_ros_bridge" 2>/dev/null || true
sleep 1

# Remove any existing joint state file
rm -f /tmp/joint_states.json 2>/dev/null || true

# Check if ROS2 is available
if ! command -v ros2 &> /dev/null; then
    echo "❌ ERROR: ros2 command not found. Please source your ROS2 environment."
    exit 1
fi

# Check if /joint_states topic exists
echo "🔍 Checking for /joint_states topic..."
if ! timeout 5 ros2 topic list | grep -q "/joint_states"; then
    echo "⚠️  WARNING: /joint_states topic not found. Make sure MoveIt is running."
    echo "   You can start MoveIt with: ros2 launch ur_simulation_gazebo ur_simulation.launch.py"
fi

# Start the ROS2 bridge node
echo "🌉 Starting ROS2 bridge node..."
cd /home/luca/Documents/GitHub/adaptive_robot_planning/real_robot
python3 moveit_to_pybullet_bridge.py &
BRIDGE_PID=$!

# Wait a moment for the bridge to initialize
sleep 2

# Start the HYBRID PyBullet simulation
echo "🤖 Starting HYBRID PyBullet simulation..."
python3 main_sim_ros_bridge_hybrid.py &
PYBULLET_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping HYBRID system..."
    kill $BRIDGE_PID 2>/dev/null || true
    kill $PYBULLET_PID 2>/dev/null || true
    rm -f /tmp/joint_states.json 2>/dev/null || true
    echo "✅ HYBRID system stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo ""
echo "✅ HYBRID system launched successfully!"
echo "   - ROS2 Bridge PID: $BRIDGE_PID"
echo "   - Hybrid PyBullet Sim PID: $PYBULLET_PID"
echo ""
echo "🎯 HYBRID FEATURES:"
echo "   - Buffers 30 trajectory points (~1.5 seconds)"
echo "   - Smoother execution with controlled rate"
echo "   - More robust to network lags"
echo "   - Detailed buffer status logging"
echo ""
echo "💡 The PyBullet robot will now follow MoveIt with buffered trajectory execution."
echo "   Press Ctrl+C to stop the system."
echo ""

# Wait for processes to finish
wait $BRIDGE_PID $PYBULLET_PID
