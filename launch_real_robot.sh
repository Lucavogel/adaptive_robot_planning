#!/bin/bash

# ==============================================================================
# LAUNCH REAL ROBOT SYSTEM - MoveIt to Real UR5 Robot Synchronization
# ==============================================================================
# This script launches the system to synchronize a real UR5 robot with MoveIt
# joint states from ROS2.
#
# Prerequisites:
# - ROS2 environment sourced
# - MoveIt running (robot should be publishing on /joint_states)
# - Real robot connected and powered on
# - Robot controller permissions configured
#
# Usage: ./launch_real_robot.sh
# ==============================================================================

echo "🤖 Starting MoveIt to Real Robot Synchronization System..."

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "moveit_to_pybullet_bridge.py" 2>/dev/null || true
pkill -f "main.py" 2>/dev/null || true
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

# Safety check
echo "⚠️  SAFETY CHECK: Make sure the real robot is:"
echo "   - Powered on and connected"
echo "   - In a safe position"
echo "   - Emergency stop is accessible"
echo "   - Work area is clear"
echo ""
read -p "Continue with real robot? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted by user."
    exit 1
fi

# Start the ROS2 bridge node
echo "🌉 Starting ROS2 bridge node..."
cd /home/luca/Documents/GitHub/adaptive_robot_planning/real_robot
python3 moveit_to_pybullet_bridge.py &
BRIDGE_PID=$!

# Wait a moment for the bridge to initialize
sleep 2

# Start the real robot controller
echo "🤖 Starting real robot controller..."
python3 main.py &
ROBOT_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping system..."
    kill $BRIDGE_PID 2>/dev/null || true
    kill $ROBOT_PID 2>/dev/null || true
    rm -f /tmp/joint_states.json 2>/dev/null || true
    echo "✅ System stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo ""
echo "✅ Real robot system launched successfully!"
echo "   - ROS2 Bridge PID: $BRIDGE_PID"
echo "   - Robot Controller PID: $ROBOT_PID"
echo ""
echo "💡 The real robot should now follow MoveIt joint commands."
echo "   ⚠️  SAFETY: Keep emergency stop accessible at all times!"
echo "   Press Ctrl+C to stop the system."
echo ""

# Wait for processes to finish
wait $BRIDGE_PID $ROBOT_PID
