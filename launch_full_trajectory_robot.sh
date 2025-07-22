#!/bin/bash

# Launch script for FULL TRAJECTORY real robot control
# This system executes complete MoveIt trajectories with global interpolation

echo "======================================================================="
echo "🎬 LAUNCHING FULL TRAJECTORY REAL ROBOT CONTROLLER"
echo "======================================================================="

# Configuration
WORKSPACE_DIR="/home/luca/Documents/GitHub/adaptive_robot_planning"
REAL_ROBOT_DIR="$WORKSPACE_DIR/real_robot"
UR_WS_DIR="$WORKSPACE_DIR/UR_WS"

# Cleanup function
cleanup_processes() {
    echo "🧹 Cleaning up processes..."
    
    # Kill trajectory bridge
    pkill -f "moveit_trajectory_bridge.py" 2>/dev/null
    
    # Kill robot controller
    pkill -f "main_full_trajectory.py" 2>/dev/null
    
    # Kill any ROS2 processes
    pkill -f "ros2" 2>/dev/null
    
    # Remove old data files
    rm -f /tmp/moveit_full_trajectory.json
    
    echo "✅ Cleanup complete"
}

# Set up cleanup on exit
trap cleanup_processes EXIT INT TERM

# Step 1: Check USB connection
echo "🔌 Checking USB connection..."
if [ ! -e "/dev/ttyACM0" ]; then
    echo "❌ ERROR: Robot not connected to /dev/ttyACM0"
    echo "   Please connect the Lynx robot USB cable and try again"
    exit 1
fi
echo "✅ Robot connected on /dev/ttyACM0"

# Step 2: Clean old data
echo "🧹 Cleaning old trajectory data..."
cleanup_processes
sleep 1

# Step 3: Check ROS2 installation
echo "🤖 Checking ROS2 installation..."
if ! command -v ros2 &> /dev/null; then
    echo "❌ ERROR: ROS2 not found. Please source your ROS2 installation:"
    echo "   source /opt/ros/humble/setup.bash"
    exit 1
fi
echo "✅ ROS2 found"

# Step 4: Source ROS2 workspace
echo "📦 Setting up ROS2 workspace..."
cd "$UR_WS_DIR" || {
    echo "❌ ERROR: Cannot access ROS2 workspace: $UR_WS_DIR"
    exit 1
}

# Source ROS2
source /opt/ros/humble/setup.bash
source install/setup.bash

echo "✅ ROS2 workspace ready"

# Step 5: Check for MoveIt
echo "🎯 Checking MoveIt availability..."
if ! ros2 pkg list | grep -q moveit; then
    echo "❌ ERROR: MoveIt not found in ROS2 installation"
    echo "   Please install MoveIt: sudo apt install ros-humble-moveit"
    exit 1
fi
echo "✅ MoveIt found"

# Step 6: Safety confirmation
echo ""
echo "⚠️  SAFETY CHECKS:"
echo "   1. Is the robot in a safe position?"
echo "   2. Is the workspace clear of obstacles?"
echo "   3. Are you ready to stop the robot if needed (CTRL-C)?"
echo "   4. Is MoveIt running with the Lynx robot model?"
echo ""
read -p "🔒 Are all safety checks complete? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Safety checks not confirmed. Exiting."
    exit 1
fi

echo "✅ Safety confirmed"

# Step 7: Launch trajectory bridge in background
echo ""
echo "🌉 Starting MoveIt TRAJECTORY bridge..."
cd "$REAL_ROBOT_DIR"
python3 moveit_trajectory_bridge.py &
BRIDGE_PID=$!

# Give bridge time to start
sleep 3

# Check if bridge started successfully
if ! kill -0 $BRIDGE_PID 2>/dev/null; then
    echo "❌ ERROR: Trajectory bridge failed to start"
    exit 1
fi
echo "✅ Trajectory bridge running (PID: $BRIDGE_PID)"

# Step 8: Launch robot controller
echo ""
echo "🤖 Starting FULL TRAJECTORY robot controller..."
echo "   📂 Trajectory data: /tmp/moveit_full_trajectory.json"
echo "   🎬 Mode: Complete trajectory execution with global interpolation"
echo "   ⚠️  Use CTRL-C to stop safely"
echo ""

sleep 2
echo "🚀 LAUNCHING ROBOT CONTROLLER..."

# Run the trajectory controller
python3 main_full_trajectory.py

# This point is reached when the controller exits
echo ""
echo "🛑 Robot controller stopped"

# Cleanup is handled by trap
