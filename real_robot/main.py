#!/usr/bin/env python3
"""
Real robot controller that follows MoveIt robot movements via ROS bridge.
This script reads joint positions from the ROS bridge and applies them to the real robot.
"""

import logging
import numpy as np
import time
import threading
import json
import os

from robot import Robot
from safety import SafetyWatchdog
# Removed NatNet/OptiTrack imports - not needed
# from optitrack import NatNetDataHandler, run_natnet_client_in_thread
import rl_config # Import the configuration file

class ROSBridgeDataReader:
    """
    Reads joint position data from the ROS bridge data file for the real robot.
    """
    
    def __init__(self, data_file_path='/tmp/moveit_to_pybullet_data.json'):
        self.data_file_path = data_file_path
        self.latest_joint_positions = None
        self.latest_joint_names = []
        self.latest_timestamp = 0
        self.data_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        
    def start_reading(self, update_interval=0.1):
        """Start reading data from the ROS bridge in a separate thread."""
        if self.running:
            print("[ROSBridge] Already running.")
            return
            
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, 
                                             args=(update_interval,), 
                                             daemon=True)
        self.reader_thread.start()
        print(f"[ROSBridge] Started reading from {self.data_file_path}")
        
    def stop_reading(self):
        """Stop reading data."""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
        print("[ROSBridge] Stopped reading.")
        
    def _read_loop(self, update_interval):
        """Main reading loop."""
        while self.running:
            try:
                if os.path.exists(self.data_file_path):
                    with open(self.data_file_path, 'r') as f:
                        data = json.load(f)
                        
                    # Check if data is newer than what we have
                    if data['timestamp'] > self.latest_timestamp:
                        with self.data_lock:
                            self.latest_joint_positions = data.get('joint_positions')
                            self.latest_joint_names = data.get('joint_names', [])
                            self.latest_timestamp = data['timestamp']
                            
                        if self.latest_joint_positions:
                            # Only log if positions actually changed
                            if self.latest_joint_positions != getattr(self, '_last_logged_positions', None):
                                print(f"[ROSBridge] New joint positions: {[f'{pos:.1f}°' for pos in self.latest_joint_positions]}")
                                self._last_logged_positions = self.latest_joint_positions.copy()
                            
                else:
                    print(f"[ROSBridge] Waiting for data file: {self.data_file_path}")
                    
            except Exception as e:
                print(f"[ROSBridge] Error reading data: {e}")
                
            time.sleep(update_interval)
            
    def get_latest_joint_positions(self):
        """Get the latest joint positions thread-safely."""
        with self.data_lock:
            return self.latest_joint_positions.copy() if self.latest_joint_positions else None
            
    def get_joint_names(self):
        """Get the joint names."""
        with self.data_lock:
            return self.latest_joint_names.copy()


def map_moveit_joints_to_real_robot(moveit_positions, moveit_joint_names, real_robot_joint_count=6):
    """
    Maps MoveIt joint positions to real robot joint order with offset compensation.
    
    Args:
        moveit_positions: List of joint positions from MoveIt (in degrees)
        moveit_joint_names: List of joint names from MoveIt
        real_robot_joint_count: Number of joints in real robot
        
    Returns:
        List of joint positions in real robot order, or None if mapping fails
    """
    if not moveit_positions or not moveit_joint_names:
        return None
        
    # Expected UR5 joint names in MoveIt (adjust if different)
    ur5_joint_names = [
        'shoulder_pan_joint',      # Joint 0
        'shoulder_lift_joint',     # Joint 1
        'elbow_joint',             # Joint 2
        'wrist_1_joint',           # Joint 3
        'wrist_2_joint',           # Joint 4
        'wrist_3_joint'            # Joint 5
    ]
    
    # Offset compensation for real robot home position
    # Adjust these values based on your real robot's actual home position
    joint_offsets = [0, 0, 0, 0, 0, 0]  # Degrees - adjust as needed
    
    # Create mapping from MoveIt joint names to positions
    joint_dict = dict(zip(moveit_joint_names, moveit_positions))
    
    # Map to real robot order with offset compensation
    real_robot_positions = []
    for i, joint_name in enumerate(ur5_joint_names):
        if joint_name in joint_dict:
            # Apply offset compensation
            compensated_position = joint_dict[joint_name] + joint_offsets[i]
            real_robot_positions.append(compensated_position)
        else:
            print(f"[ROSBridge] Warning: Joint {joint_name} not found in MoveIt data")
            return None
            
    return real_robot_positions

if __name__ == '__main__':
    # Initialize real robot
    robo = Robot(portname=rl_config.PORT)
    if not robo.init_bus():
        print("[Main] Failed to open serial port. Exiting.")
        exit(1)
    robo.init_motors()

    # Initialize safety watchdog (without NatNet)
    watchdog = SafetyWatchdog(
        robot_controller=robo,
        natnet_data_handler=None,  # No OptiTrack needed
        joint_limits=rl_config.JOINT_LIMITS,
        marker_radii=rl_config.MARKER_RADII,
    )
    robo.joint_watchdog = watchdog
    watchdog.start(check_interval=rl_config.WATCHDOG_INTERVAL)
    
    # Initialize ROS bridge reader
    ros_bridge = ROSBridgeDataReader()
    ros_bridge.start_reading(update_interval=0.05)  # Read at 20Hz
    
    print("[Main] Real robot initialized (without OptiTrack). Waiting for MoveIt commands...")
    print("[Main] Start your MoveIt planning and the robot will follow!")
    
    try:
        last_command_time = 0
        last_moveit_positions = None  # Pour détecter les changements
        
        while True:
            if watchdog._exception_event.is_set():
                print("\n[Main] Watchdog thread reported a critical exception. Stopping.")
                robo.enter_emergency_recovery()
                break
                
            # Get latest joint positions from ROS bridge
            moveit_positions = ros_bridge.get_latest_joint_positions()
            moveit_joint_names = ros_bridge.get_joint_names()
            
            if moveit_positions and moveit_joint_names:
                # Check if positions have changed (only move if there's a change)
                if last_moveit_positions is None or moveit_positions != last_moveit_positions:
                    # Map MoveIt joints to real robot order
                    real_robot_positions = map_moveit_joints_to_real_robot(
                        moveit_positions, moveit_joint_names
                    )
                    
                    if real_robot_positions:
                        # Apply safety limits
                        cmd = []
                        for j, angle in enumerate(real_robot_positions):
                            if j < len(rl_config.JOINT_LIMITS):
                                min_limit, max_limit = rl_config.JOINT_LIMITS[j]
                                clamped_angle = np.clip(angle, min_limit, max_limit)
                                cmd.append(float(clamped_angle))
                                
                                if abs(clamped_angle - angle) > 0.1:
                                    print(f"[Main] WARNING: Joint {j} clamped from {angle:.2f}° to {clamped_angle:.2f}°")
                            else:
                                cmd.append(float(angle))
                        
                        # Send command to real robot
                        print(f"[Main] New MoveIt command received!")
                        print(f"[Main] MoveIt positions: {[f'{pos:.2f}°' for pos in moveit_positions]}")
                        print(f"[Main] Real robot positions (clamped): {[f'{pos:.2f}°' for pos in cmd]}")
                        
                        try:
                            robo.move_abs_with_speed(cmd, speed=rl_config.MAX_SPEED)
                            print(f"[Main] move_abs_with_speed completed.")
                            last_command_time = time.time()
                            last_moveit_positions = moveit_positions.copy()
                                
                            # Show current joint angles
                            current_joint_angles = robo.get_Position()
                            if current_joint_angles:
                                angles_str = [f'{angle[0]:.2f}°' if angle[0] is not None else 'N/A' 
                                            for angle in current_joint_angles]
                                print(f"[Main] Current Joint Angles: {angles_str}")
                                print("---")
                        except Exception as e:
                            print(f"[Main] Error in move_abs_with_speed: {e}")
                            continue
                    
            time.sleep(0.05)  # 20Hz update rate
            
    except KeyboardInterrupt:
        print("\n[Main] CTRL-C detected. Shutting down...")
        robo.enter_emergency_recovery()
    except Exception as e:
        print(f"[Main] Exception in main loop: {e}")
        robo.enter_emergency_recovery()
    finally:
        print("[Main] Cleaning up...")
        ros_bridge.stop_reading()
        watchdog.stop()
        robo.shutdown()
        print("[Main] Shutdown complete.")
