#!/bin/bash
# Launch script for full trajectory simulation testing
# This tests the new trajectory system in PyBullet simulation

echo "🚀 MoveIt Full Trajectory Simulation Launch"
echo "=================================================="

# Set working directory
cd /home/luca/Documents/GitHub/adaptive_robot_planning

# Check if ROS2 is sourced
if [ -z "$ROS_DISTRO" ]; then
    echo "❌ ROS2 not sourced. Please run:"
    echo "   source /opt/ros/humble/setup.bash"
    exit 1
fi

# Check if workspace is built
if [ ! -d "UR_WS/install" ]; then
    echo "❌ Workspace not built. Please run:"
    echo "   cd UR_WS && colcon build"
    exit 1
fi

# Source workspace
echo "📦 Sourcing ROS2 workspace..."
source UR_WS/install/setup.bash

# Clean up old data files
echo "🧹 Cleaning up old data files..."
rm -f /tmp/moveit_full_trajectory.json
rm -f /tmp/moveit_to_pybullet_data.json

# Check for required files
BRIDGE_FILE="real_robot/moveit_trajectory_bridge.py"
SIM_FILE="real_robot/main_full_trajectory_sim.py"

if [ ! -f "$BRIDGE_FILE" ]; then
    echo "❌ Bridge file not found: $BRIDGE_FILE"
    exit 1
fi

if [ ! -f "$SIM_FILE" ]; then
    echo "❌ Simulation file not found: $SIM_FILE"
    exit 1
fi

echo "✅ All required files found"

# Function to cleanup processes
cleanup() {
    echo -e "\n🛑 Shutting down processes..."
    pkill -f "moveit_trajectory_bridge"
    pkill -f "main_full_trajectory_sim"
    pkill -f "move_group"
    pkill -f "rviz"
    echo "✅ Cleanup complete"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

echo -e "\n🎯 Starting Full Trajectory System..."
echo "   This will test the NEW trajectory system that captures"
echo "   the COMPLETE MoveIt planned path and executes it smoothly."

# Start ROS2 bridge for trajectory capture
echo -e "\n1️⃣ Starting MoveIt trajectory bridge..."
python3 real_robot/moveit_trajectory_bridge.py &
BRIDGE_PID=$!
sleep 3

# Start MoveIt
echo -e "\n2️⃣ Starting MoveIt with planning capabilities..."
ros2 launch ur_simulation_gazebo ur_sim_moveit.launch.py &
MOVEIT_PID=$!
sleep 8

# Check if bridge is still running
if ! kill -0 $BRIDGE_PID 2>/dev/null; then
    echo "❌ Bridge process died. Check for errors."
    exit 1
fi

# Start simulation controller
echo -e "\n3️⃣ Starting PyBullet simulation with full trajectory execution..."
echo "   📊 This will show global interpolation across the entire planned path"
echo "   🎯 The robot will follow the exact MoveIt trajectory, not just the goal"
echo ""
python3 real_robot/main_full_trajectory_sim.py &
SIM_PID=$!

# Wait for all processes
echo -e "\n✅ Full Trajectory Simulation System Running!"
echo "=================================================="
echo "📋 How to test:"
echo "   1. In MoveIt (RViz), plan a complex trajectory"
echo "   2. Watch the PyBullet simulation execute the COMPLETE path"
echo "   3. Compare with old system - this should be much smoother!"
echo ""
echo "🔍 Monitor files:"
echo "   📂 /tmp/moveit_full_trajectory.json - Complete trajectory data"
echo "   📊 Watch the interpolation steps in the simulation terminal"
echo ""
echo "Press Ctrl+C to stop all processes"
echo "=================================================="

# Wait for processes
wait $BRIDGE_PID $SIM_PID $MOVEIT_PID
