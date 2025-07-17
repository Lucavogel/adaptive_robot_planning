#!/usr/bin/env python3
"""
PyBullet simulation that follows MoveIt robot movements via ROS bridge.
This script reads joint positions from the ROS bridge and applies them to the PyBullet robot.
"""

import logging
import numpy as np
import time
import threading
import json
import os

from sim_robot import SimRobot
from safety import SafetyWatchdogSim
from sim_sensor import SimNatNetDataHandler
import rl_config

class ROSBridgeDataReader:
    """
    Reads joint position data from the ROS bridge data file.
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


def map_moveit_joints_to_pybullet(moveit_positions, moveit_joint_names, pybullet_joint_count=6):
    """
    Maps MoveIt joint positions to PyBullet joint order with offset compensation.
    
    Args:
        moveit_positions: List of joint positions from MoveIt (in degrees)
        moveit_joint_names: List of joint names from MoveIt
        pybullet_joint_count: Number of joints in PyBullet robot
        
    Returns:
        List of joint positions in PyBullet order, or None if mapping fails
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
    
    # Offset compensation: MoveIt home [0, -90, 0, 0, 0, 0] -> PyBullet home [0, 0, 0, 0, 0, 0]
    # So we need to add 90° to joint 1 (shoulder_lift_joint)
    joint_offsets = [0, 90, 0, 0, 0, 0]  # Degrees
    
    # Create mapping from MoveIt joint names to positions
    joint_dict = dict(zip(moveit_joint_names, moveit_positions))
    
    # Map to PyBullet order with offset compensation
    pybullet_positions = []
    for i, joint_name in enumerate(ur5_joint_names):
        if joint_name in joint_dict:
            # Apply offset compensation
            compensated_position = joint_dict[joint_name] + joint_offsets[i]
            pybullet_positions.append(compensated_position)
        else:
            print(f"[ROSBridge] Warning: Joint {joint_name} not found in MoveIt data")
            return None
            
    return pybullet_positions


if __name__ == '__main__':
    # Initialize PyBullet robot
    robo = SimRobot()
    if not robo.init_bus():
        print("[Main] Failed to open simulation. Exiting.")
        exit(1)
    robo.init_motors()

    # Get PyBullet related info
    pybullet_api = robo.get_pybullet_api()
    physics_client_id = robo.get_physics_client_id()
    robot_id = robo.get_robot_id()
    ee_link_id = robo.get_end_effector_link_id()
    pybullet_api_lock = robo.get_pybullet_api_lock()

    # Initialize simulated sensor
    sim_data_manager = SimNatNetDataHandler(
        p_api=pybullet_api,
        physics_client_id=physics_client_id,
        robot_id=robot_id,
        end_effector_link_id=ee_link_id,
        pybullet_api_lock=pybullet_api_lock,
        verbose=False
    )
    
    # Initialize safety watchdog
    watchdog = SafetyWatchdogSim(
        robot_controller=robo,
        natnet_data_handler=sim_data_manager,
        joint_limits=rl_config.JOINT_LIMITS,
        marker_radii=rl_config.MARKER_RADII,
    )
    robo.joint_watchdog = watchdog
    watchdog.start(check_interval=rl_config.WATCHDOG_INTERVAL)
    
    # Initialize ROS bridge reader
    ros_bridge = ROSBridgeDataReader()
    ros_bridge.start_reading(update_interval=0.05)  # Read at 20Hz
    
    print("[Main] PyBullet robot initialized. Waiting for MoveIt commands...")
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
                    # Map MoveIt joints to PyBullet order
                    pybullet_positions = map_moveit_joints_to_pybullet(
                        moveit_positions, moveit_joint_names
                    )
                    
                    if pybullet_positions:
                        # Send command to PyBullet robot
                        print(f"[Main] New MoveIt command received!")
                        print(f"[Main] MoveIt positions: {[f'{pos:.2f}°' for pos in moveit_positions]}")
                        print(f"[Main] PyBullet positions (with offset): {[f'{pos:.2f}°' for pos in pybullet_positions]}")
                        robo.move_abs_with_speed(pybullet_positions, speed=rl_config.MAX_SPEED)
                        last_command_time = time.time()
                        last_moveit_positions = moveit_positions.copy()
                        
                        # Show current end-effector position
                        if sim_data_manager.latest_relative_pos is not None:
                            pos = sim_data_manager.latest_relative_pos
                            print(f'[Main] EEF position: X={pos[0]:.4f}, Y={pos[1]:.4f}, Z={pos[2]:.4f}')
                            
                        # Show current joint angles
                        current_joint_angles = robo.get_Position()
                        if current_joint_angles:
                            angles_str = [f'{angle[0]:.2f}°' if angle[0] is not None else 'N/A' 
                                        for angle in current_joint_angles]
                            print(f"[Main] Current Joint Angles: {angles_str}")
                            print("---")
                        
            # Always step the simulation to keep it running
            with pybullet_api_lock:
                pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                    
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
