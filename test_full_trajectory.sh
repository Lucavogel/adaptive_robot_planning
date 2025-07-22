#!/bin/bash
# Simple test script for full trajectory system

echo "🧪 Testing Full Trajectory System Components"
echo "=========================================="

cd /home/luca/Documents/GitHub/adaptive_robot_planning

# Source ROS2
source /opt/ros/humble/setup.bash
source UR_WS/install/setup.bash

echo "✅ Environment sourced"

# Test 1: Start trajectory bridge in background
echo "1️⃣ Starting trajectory bridge..."
python3 real_robot/moveit_trajectory_bridge.py &
BRIDGE_PID=$!
echo "   Bridge PID: $BRIDGE_PID"

sleep 5

# Test 2: Start simulation
echo "2️⃣ Starting simulation..."
python3 real_robot/main_full_trajectory_sim.py &
SIM_PID=$!
echo "   Simulation PID: $SIM_PID"

sleep 5

# Test 3: Check if processes are running
echo "3️⃣ Checking processes..."
if ps -p $BRIDGE_PID > /dev/null; then
   echo "   ✅ Bridge is running (PID: $BRIDGE_PID)"
else
   echo "   ❌ Bridge is not running"
fi

if ps -p $SIM_PID > /dev/null; then
   echo "   ✅ Simulation is running (PID: $SIM_PID)"
else
   echo "   ❌ Simulation is not running"
fi

echo "4️⃣ Test complete. Both processes should be running."
echo "   Now you can start MoveIt to test trajectory planning."
echo "   Press Enter to stop all processes..."
read

# Cleanup
echo "🧹 Stopping processes..."
kill $BRIDGE_PID $SIM_PID 2>/dev/null
sleep 2
pkill -f "moveit_trajectory_bridge" 2>/dev/null
pkill -f "main_full_trajectory_sim" 2>/dev/null

echo "✅ Test complete"
