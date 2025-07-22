#!/usr/bin/env python3
"""
ROS Joint Reader for Real Robot
Reads joint positions from the ROS bridge JSON file and provides them to the real robot controller.
"""

import json
import os
import time
import threading
from typing import List, Optional


class ROSJointReader:
    """
    Reads joint position data from the ROS bridge JSON file for the real robot.
    """
    
    def __init__(self, data_file_path='/tmp/joint_states.json'):
        self.data_file_path = data_file_path
        self.latest_joint_positions = None
        self.latest_joint_names = []
        self.latest_timestamp = 0
        self.data_lock = threading.Lock()
        self.data_freshness_timeout = 2.0  # seconds
        
    def wait_for_data(self, timeout_seconds=10.0):
        """
        Wait for ROS data to be available.
        
        Args:
            timeout_seconds: Maximum time to wait for data
            
        Returns:
            bool: True if data is available, False if timeout
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout_seconds:
            if os.path.exists(self.data_file_path):
                try:
                    with open(self.data_file_path, 'r') as f:
                        data = json.load(f)
                    
                    if data.get('joint_positions') and data.get('joint_names'):
                        print(f"[ROSJointReader] ROS data detected: {len(data['joint_positions'])} joints")
                        return True
                        
                except Exception as e:
                    print(f"[ROSJointReader] Error reading initial data: {e}")
                    
            time.sleep(0.5)
            
        return False
        
    def get_latest_joint_angles(self):
        """
        Get the latest joint angles from ROS bridge.
        
        Returns:
            List of joint angles in degrees, or None if no data available
        """
        try:
            if not os.path.exists(self.data_file_path):
                return None
                
            with open(self.data_file_path, 'r') as f:
                data = json.load(f)
                
            # Update our local cache if data is newer
            if data['timestamp'] > self.latest_timestamp:
                with self.data_lock:
                    self.latest_joint_positions = data.get('joint_positions')
                    self.latest_joint_names = data.get('joint_names', [])
                    self.latest_timestamp = data['timestamp']
                    
            # Return the latest joint positions
            with self.data_lock:
                if self.latest_joint_positions:
                    # Map MoveIt joints to real robot order with offset compensation
                    return self._map_moveit_to_real_robot(
                        self.latest_joint_positions, 
                        self.latest_joint_names
                    )
                    
        except Exception as e:
            print(f"[ROSJointReader] Error reading joint data: {e}")
            
        return None
        
    def is_data_fresh(self):
        """
        Check if the data is fresh (recently updated).
        
        Returns:
            bool: True if data is fresh, False if stale
        """
        if self.latest_timestamp == 0:
            return False
            
        current_time = time.time()
        data_age = current_time - self.latest_timestamp
        
        return data_age < self.data_freshness_timeout
        
    def _map_moveit_to_real_robot(self, moveit_positions, moveit_joint_names):
        """
        Map MoveIt joint positions to real robot order with offset compensation.
        
        Args:
            moveit_positions: List of joint positions from MoveIt (in degrees)
            moveit_joint_names: List of joint names from MoveIt
            
        Returns:
            List of joint positions in real robot order, or None if mapping fails
        """
        if not moveit_positions or not moveit_joint_names:
            return None
            
        # Expected UR5 joint names in MoveIt
        ur5_joint_names = [
            'shoulder_pan_joint',      # Joint 0
            'shoulder_lift_joint',     # Joint 1
            'elbow_joint',             # Joint 2
            'wrist_1_joint',           # Joint 3
            'wrist_2_joint',           # Joint 4
            'wrist_3_joint'            # Joint 5
        ]
        
        # Offset compensation for real robot
        # MoveIt home position might be different from real robot home position
        # Adjust these offsets based on your robot's actual home position
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
                print(f"[ROSJointReader] Warning: Joint {joint_name} not found in MoveIt data")
                return None
                
        return real_robot_positions
        
    def get_joint_names(self):
        """Get the joint names."""
        with self.data_lock:
            return self.latest_joint_names.copy()


# Test function
if __name__ == '__main__':
    print("Testing ROSJointReader...")
    
    reader = ROSJointReader()
    
    # Test waiting for data
    print("Waiting for ROS data...")
    if reader.wait_for_data(timeout_seconds=5.0):
        print("✅ ROS data detected!")
        
        # Test reading joint angles
        for i in range(10):
            angles = reader.get_latest_joint_angles()
            fresh = reader.is_data_fresh()
            
            if angles:
                print(f"[{i}] Joint angles: {[f'{a:.2f}°' for a in angles]} (fresh: {fresh})")
            else:
                print(f"[{i}] No joint angles available")
                
            time.sleep(0.5)
            
    else:
        print("❌ No ROS data detected. Make sure the bridge is running.")
