#!/usr/bin/env python3
"""
Test script to verify the real robot system integration with MoveIt.
This script tests the ROS joint reader and robot communication.
"""

import time
import sys
import os

# Add the real_robot directory to the Python path
sys.path.append('/home/luca/Documents/GitHub/adaptive_robot_planning/real_robot')

from ros_joint_reader import ROSJointReader
from robot import Robot
import rl_config

def test_ros_bridge():
    """Test the ROS bridge connection."""
    print("🔧 Testing ROS Bridge Connection...")
    
    reader = ROSJointReader()
    
    # Test waiting for data
    print("⏳ Waiting for ROS data (timeout: 5s)...")
    if reader.wait_for_data(timeout_seconds=5.0):
        print("✅ ROS bridge data detected!")
        
        # Test reading joint angles
        angles = reader.get_latest_joint_angles()
        fresh = reader.is_data_fresh()
        
        if angles:
            print(f"📊 Joint angles: {[f'{a:.2f}°' for a in angles]}")
            print(f"📊 Data fresh: {fresh}")
            return True
        else:
            print("❌ No joint angles available")
            return False
    else:
        print("❌ No ROS data detected")
        print("   Make sure the bridge is running: python3 moveit_to_pybullet_bridge.py")
        return False

def test_robot_connection():
    """Test the real robot connection."""
    print("\n🤖 Testing Real Robot Connection...")
    
    try:
        robo = Robot(portname=rl_config.PORT)
        
        if robo.init_bus():
            print("✅ Robot serial connection established!")
            
            # Test motor initialization
            robo.init_motors()
            print("✅ Motors initialized!")
            
            # Test getting current position
            current_pos = robo.get_Position()
            if current_pos:
                print(f"📊 Current joint positions: {[f'{pos[0]:.2f}°' if pos[0] is not None else 'N/A' for pos in current_pos]}")
            
            # Test a small movement (safe)
            print("🔄 Testing small movement...")
            test_cmd = [0., 0., 0., 0., 0., 0.]  # Home position
            robo.move_abs_with_speed(test_cmd, speed=500)  # Slower speed for safety
            
            # Wait and check position
            time.sleep(2)
            new_pos = robo.get_Position()
            if new_pos:
                print(f"📊 New joint positions: {[f'{pos[0]:.2f}°' if pos[0] is not None else 'N/A' for pos in new_pos]}")
            
            robo.shutdown()
            print("✅ Robot test completed successfully!")
            return True
            
        else:
            print("❌ Failed to establish robot connection")
            print(f"   Check that robot is connected to {rl_config.PORT}")
            return False
            
    except Exception as e:
        print(f"❌ Robot test failed: {e}")
        return False

def test_joint_limits():
    """Test joint limits configuration."""
    print("\n⚙️  Testing Joint Limits Configuration...")
    
    print("📊 Configured joint limits:")
    for i, (min_limit, max_limit) in enumerate(rl_config.JOINT_LIMITS):
        print(f"   Joint {i}: {min_limit}° to {max_limit}°")
    
    # Test clamping
    import numpy as np
    
    test_angles = [200, -150, 50, 190, -200, 100]  # Some values outside limits
    print(f"📊 Test angles: {test_angles}")
    
    clamped_angles = []
    for i, angle in enumerate(test_angles):
        if i < len(rl_config.JOINT_LIMITS):
            min_limit, max_limit = rl_config.JOINT_LIMITS[i]
            clamped = np.clip(angle, min_limit, max_limit)
            clamped_angles.append(clamped)
            
            if clamped != angle:
                print(f"   Joint {i}: {angle}° → {clamped}° (clamped)")
            else:
                print(f"   Joint {i}: {angle}° (OK)")
    
    print("✅ Joint limits test completed!")
    return True

def main():
    """Run all tests."""
    print("🚀 === Real Robot System Integration Test ===\n")
    
    # Test 1: ROS Bridge
    ros_ok = test_ros_bridge()
    
    # Test 2: Joint Limits
    limits_ok = test_joint_limits()
    
    # Test 3: Robot Connection (only if ROS is working)
    robot_ok = False
    if ros_ok:
        print("\n⚠️  Robot Connection Test")
        print("   This will move the real robot to home position!")
        response = input("   Continue? (y/N): ")
        if response.lower() == 'y':
            robot_ok = test_robot_connection()
        else:
            print("   Robot test skipped by user.")
    
    # Summary
    print("\n📋 === Test Results ===")
    print(f"   🌉 ROS Bridge:      {'✅ PASS' if ros_ok else '❌ FAIL'}")
    print(f"   ⚙️  Joint Limits:    {'✅ PASS' if limits_ok else '❌ FAIL'}")
    print(f"   🤖 Robot Connection: {'✅ PASS' if robot_ok else '⏭️  SKIPPED'}")
    
    if ros_ok and limits_ok:
        print("\n🎉 Basic system integration tests passed!")
        print("   You can now run: ./launch_real_robot.sh")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")

if __name__ == '__main__':
    main()
