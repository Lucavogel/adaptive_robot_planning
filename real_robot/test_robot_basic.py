#!/usr/bin/env python3
"""
Basic robot hardware test to check if motors are responding.
"""

import time
from robot import Robot
import rl_config

def test_robot_basic():
    print("[Test] Starting basic robot hardware test...")
    
    # Initialize robot
    robo = Robot(portname=rl_config.PORT)
    if not robo.init_bus():
        print("[Test] ❌ Failed to open serial port.")
        return False
    
    robo.init_motors()
    print("[Test] ✅ Robot initialized successfully")
    
    # Get initial position
    print("[Test] Reading initial joint positions...")
    initial_pos = robo.get_Position()
    if initial_pos:
        angles = [f'{angle[0]:.2f}°' if angle[0] is not None else 'N/A' for angle in initial_pos]
        print(f"[Test] Initial position: {angles}")
    else:
        print("[Test] ❌ Could not read initial position")
        return False
    
    # Test small movement on joint 0 (base)
    print("[Test] Testing small movement on joint 0 (5 degrees)...")
    target_pos = [5.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # 5 degrees on base joint
    
    try:
        result = robo.move_abs_with_speed(target_pos, speed=200)
        print(f"[Test] Move command result: {result}")
        
        # Wait for movement
        time.sleep(2.0)
        
        # Check new position
        new_pos = robo.get_Position()
        if new_pos:
            angles = [f'{angle[0]:.2f}°' if angle[0] is not None else 'N/A' for angle in new_pos]
            print(f"[Test] Position after move: {angles}")
        else:
            print("[Test] ❌ Could not read new position")
            
        # Move back to home
        print("[Test] Moving back to home position...")
        robo.move_abs_with_speed([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], speed=200)
        time.sleep(2.0)
        
        final_pos = robo.get_Position()
        if final_pos:
            angles = [f'{angle[0]:.2f}°' if angle[0] is not None else 'N/A' for angle in final_pos]
            print(f"[Test] Final position: {angles}")
            
    except Exception as e:
        print(f"[Test] ❌ Error during movement test: {e}")
        return False
    finally:
        robo.shutdown()
        print("[Test] Robot shutdown complete")
    
    return True

if __name__ == '__main__':
    success = test_robot_basic()
    if success:
        print("[Test] ✅ Basic robot test completed")
    else:
        print("[Test] ❌ Basic robot test failed")
