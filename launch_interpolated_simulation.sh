#!/bin/bash

echo "🎯 Starting INTERPOLATED MoveIt to PyBullet Synchronization System..."

# Function to cleanup on exit
cleanup() {
    echo -e "\n🧹 Cleaning up processes..."
    if [ ! -z "$ROS_BRIDGE_PID" ]; then
        kill $ROS_BRIDGE_PID 2>/dev/null
        echo "  ✅ ROS Bridge stopped"
    fi
    if [ ! -z "$PYBULLET_PID" ]; then
        kill $PYBULLET_PID 2>/dev/null  
        echo "  ✅ PyBullet simulation stopped"
    fi
    echo "🎯 INTERPOLATED system stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Set up environment
export ROS_DOMAIN_ID=0

echo "🧹 Cleaning up existing processes..."
pkill -f "moveit_to_pybullet_bridge" 2>/dev/null || true
pkill -f "main_sim_interpolated" 2>/dev/null || true
rm -f /tmp/moveit_to_pybullet_data.json 2>/dev/null || true

echo "🔍 Checking for /joint_states topic..."
timeout 3 ros2 topic list | grep -q "/joint_states" || {
    echo "⚠️  WARNING: /joint_states topic not found. Make sure MoveIt is running."
    echo "   You can start MoveIt with: ros2 launch lynx_moveit_config_2 demo.launch.py"
}

echo "🌉 Starting ROS2 bridge node..."
cd /home/luca/Documents/GitHub/adaptive_robot_planning/real_robot
python3 moveit_to_pybullet_bridge.py &
ROS_BRIDGE_PID=$!
sleep 2

echo "🎯 Starting INTERPOLATED PyBullet simulation..."
cd /home/luca/Documents/GitHub/adaptive_robot_planning/real_robot
python3 sim_block_interpolation.py &
PYBULLET_PID=$!
sleep 1

echo ""
echo "✅ INTERPOLATED system launched successfully!"
echo "   - ROS2 Bridge PID: $ROS_BRIDGE_PID"
echo "   - Interpolated PyBullet Sim PID: $PYBULLET_PID"
echo ""
echo "� SIMULATION INTERPOLATION FEATURES:"
echo "   - Conservative interpolation (2-10 steps based on movement size)"
echo "   - Adaptive speed control per step"
echo "   - Safety-focused timing (80ms between steps)"
echo "   - Position tolerance: 1.0° (prevents micro-movements)"
echo "   - Startup delay: 2.0s (prevents immediate large movements)"
echo "   - Automatic safety limit clamping"
echo ""
echo "💡 The simulation will now follow MoveIt with SMOOTH INTERPOLATED movement."
echo "   The robot waits 2 seconds before processing commands to avoid startup jumps."
echo "   Press Ctrl+C to stop the system safely."

# Wait for processes to finish
wait
