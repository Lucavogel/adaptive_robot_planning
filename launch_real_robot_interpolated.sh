#!/bin/bash

echo "🤖 Starting INTERPOLATED MoveIt to REAL ROBOT System..."

# Function to cleanup on exit
cleanup() {
    echo -e "\n🧹 Cleaning up processes..."
    if [ ! -z "$ROS_BRIDGE_PID" ]; then
        kill $ROS_BRIDGE_PID 2>/dev/null
        echo "  ✅ ROS Bridge stopped"
    fi
    if [ ! -z "$REAL_ROBOT_PID" ]; then
        kill $REAL_ROBOT_PID 2>/dev/null  
        echo "  ✅ Real robot controller stopped"
    fi
    echo "🤖 INTERPOLATED real robot system stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Set up environment
export ROS_DOMAIN_ID=0

echo "🧹 Cleaning up existing processes..."
pkill -f "moveit_to_pybullet_bridge" 2>/dev/null || true
pkill -f "main_real_interpolation" 2>/dev/null || true
pkill -f "main.py" 2>/dev/null || true

echo "🗑️  Removing old MoveIt data to prevent unwanted movements..."
rm -f /tmp/moveit_to_pybullet_data.json 2>/dev/null || true

echo "🔍 Checking for /joint_states topic..."
timeout 3 ros2 topic list | grep -q "/joint_states" || {
    echo "⚠️  WARNING: /joint_states topic not found. Make sure MoveIt is running."
    echo "   You can start MoveIt with: ros2 launch lynx_moveit_config_2 demo.launch.py"
}

echo "🔌 Checking robot connection..."
if [ ! -c "/dev/ttyUSB0" ] && [ ! -c "/dev/ttyACM0" ]; then
    echo "⚠️  WARNING: No robot USB connection found (/dev/ttyUSB0 or /dev/ttyACM0)"
    echo "   Make sure the robot is connected and powered on."
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Exiting..."
        exit 1
    fi
fi

echo "🌉 Starting ROS2 bridge node..."
cd /home/luca/Documents/GitHub/adaptive_robot_planning/real_robot
python3 moveit_to_pybullet_bridge.py &
ROS_BRIDGE_PID=$!
sleep 2

echo "🤖 Starting INTERPOLATED real robot controller..."
cd /home/luca/Documents/GitHub/adaptive_robot_planning/real_robot
python3 main_real_interpolation.py &
REAL_ROBOT_PID=$!
sleep 2

echo ""
echo "✅ INTERPOLATED real robot system launched successfully!"
echo "   - ROS2 Bridge PID: $ROS_BRIDGE_PID"
echo "   - Real Robot Controller PID: $REAL_ROBOT_PID"
echo ""
echo "🤖 REAL ROBOT INTERPOLATION FEATURES:"
echo "   - Conservative interpolation (2-10 steps based on movement size)"
echo "   - Adaptive speed control per step (200-400 speed units)"
echo "   - Safety-focused timing (150ms between steps)"
echo "   - Position tolerance: 1.0° (prevents micro-movements)"
echo "   - Automatic safety limit clamping"
echo "   - Real-time position feedback"
echo "   - Emergency recovery system"
echo ""
echo "⚠️  SAFETY REMINDERS:"
echo "   - Keep emergency stop accessible"
echo "   - Monitor robot movements visually"
echo "   - Interpolation makes movements smoother but slower"
echo "   - All joint limits are enforced automatically"
echo ""
echo "💡 The real robot will now follow MoveIt with SMOOTH INTERPOLATED movement."
echo "   Press Ctrl+C to stop the system safely."
echo ""
echo "📝 STARTUP PROCESS:"
echo "   1. The robot controller will wait for your confirmation"
echo "   2. Only NEW MoveIt commands will be followed (old data ignored)"
echo "   3. Start MoveIt planning AFTER you see the robot controller prompt"

# Wait for processes to finish
wait
