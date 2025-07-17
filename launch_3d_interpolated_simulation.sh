#!/bin/bash

# ==============================================================================
# LAUNCH 3D INTERPOLATED SIMULATION - Ultra-Smooth MoveIt to PyBullet Sync
# ==============================================================================
# This script launches the 3D INTERPOLATED version that uses 5th degree 
# polynomial interpolation for ultra-smooth robot motions.
#
# Prerequisites:
# - ROS2 environment sourced
# - MoveIt running (robot should be publishing on /joint_states)
# - PyBullet installed
# - scipy installed (pip install scipy)
#
# Usage: ./launch_3d_interpolated_simulation.sh
# ==============================================================================

echo "🎯 Starting 3D INTERPOLATED MoveIt to PyBullet Synchronization System..."

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "moveit_to_pybullet_bridge.py" 2>/dev/null || true
pkill -f "main_sim_ros_bridge" 2>/dev/null || true
sleep 1

# Remove any existing joint state file
rm -f /tmp/moveit_to_pybullet_data.json 2>/dev/null || true

# Check if ROS2 is available
if ! command -v ros2 &> /dev/null; then
    echo "❌ ERROR: ros2 command not found. Please source your ROS2 environment."
    exit 1
fi

# Check if scipy is available
if ! python3 -c "import scipy.interpolate" 2>/dev/null; then
    echo "❌ ERROR: scipy not found. Please install it with: pip install scipy"
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

# Start the 3D INTERPOLATED PyBullet simulation
echo "🎯 Starting 3D INTERPOLATED PyBullet simulation..."
python3 main_sim_ros_bridge_3d_interpolated.py &
PYBULLET_PID=$!

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping 3D INTERPOLATED system..."
    kill $BRIDGE_PID 2>/dev/null || true
    kill $PYBULLET_PID 2>/dev/null || true
    rm -f /tmp/moveit_to_pybullet_data.json 2>/dev/null || true
    echo "✅ 3D INTERPOLATED system stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo ""
echo "✅ 3D INTERPOLATED system launched successfully!"
echo "   - ROS2 Bridge PID: $BRIDGE_PID"
echo "   - 3D Interpolated PyBullet Sim PID: $PYBULLET_PID"
echo ""
echo "🎯 3D INTERPOLATED FEATURES:"
echo "   - 5th degree polynomial interpolation"
echo "   - 50 Hz ultra-smooth trajectory generation"
echo "   - Buffer size: 100 points (~2 seconds)"
echo "   - Adaptive interpolation (cubic spline fallback)"
echo "   - Real-time trajectory queue management"
echo ""
echo "🎪 ULTRA-SMOOTH MOTION: The robot will now move with cinema-quality smoothness!"
echo "   Press Ctrl+C to stop the system."
echo ""

# Wait for processes to finish
wait $BRIDGE_PID $PYBULLET_PID
