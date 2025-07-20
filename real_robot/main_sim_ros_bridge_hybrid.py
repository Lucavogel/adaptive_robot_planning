#!/usr/bin/env python3
"""
HYBRID VERSION - PyBullet simulation that follows MoveIt robot movements via ROS bridge.
This version buffers trajectory points for smoother and more robust execution.
"""

import logging
import numpy as np
import time
import threading
import json
import os
from collections import deque

from sim_robot import SimRobot
from safety import SafetyWatchdogSim
from sim_sensor import SimNatNetDataHandler
import rl_config

class HybridROSBridgeDataReader:
    """
    Hybrid approach: Reads and buffers trajectory points from ROS bridge data file.
    """
    
    def __init__(self, data_file_path='/tmp/moveit_to_pybullet_data.json', buffer_size=50, max_age_seconds=2.0):
        self.data_file_path = data_file_path
        self.buffer_size = buffer_size
        self.max_age_seconds = max_age_seconds
        self.trajectory_buffer = deque(maxlen=buffer_size)
        self.data_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        self.last_read_timestamp = 0
        
    def start_reading(self, update_interval=0.02):
        """Start reading data from the ROS bridge in a separate thread."""
        if self.running:
            print("[HybridROSBridge] Already running.")
            return
            
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, 
                                             args=(update_interval,), 
                                             daemon=True)
        self.reader_thread.start()
        print(f"[HybridROSBridge] Started reading from {self.data_file_path} (buffer size: {self.buffer_size})")
        
    def stop_reading(self):
        """Stop reading data."""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
        print("[HybridROSBridge] Stopped reading.")
        
    def _read_loop(self, update_interval):
        """Main reading loop - buffers trajectory points."""
        while self.running:
            try:
                if os.path.exists(self.data_file_path):
                    with open(self.data_file_path, 'r') as f:
                        data = json.load(f)
                        
                    # Only add new data points
                    if data['timestamp'] > self.last_read_timestamp:
                        self._add_trajectory_point(
                            data.get('joint_positions'),
                            data.get('joint_names', []),
                            data['timestamp']
                        )
                        self.last_read_timestamp = data['timestamp']
                        
                else:
                    print(f"[HybridROSBridge] Waiting for data file: {self.data_file_path}")
                    
            except Exception as e:
                print(f"[HybridROSBridge] Error reading data: {e}")
                
            time.sleep(update_interval)
            
    def _add_trajectory_point(self, positions, joint_names, timestamp):
        """Add a new trajectory point to the buffer"""
        if not positions or not joint_names:
            return
            
        with self.data_lock:
            point = {
                'positions': positions,
                'joint_names': joint_names,
                'timestamp': timestamp,
                'executed': False
            }
            self.trajectory_buffer.append(point)
            
            # Only log if significantly different from last point
            if len(self.trajectory_buffer) > 1:
                prev_point = self.trajectory_buffer[-2]
                if self._positions_differ(positions, prev_point['positions']):
                    print(f"[HybridROSBridge] Buffered new point: {[f'{pos:.1f}°' for pos in positions]}")
                    
    def _positions_differ(self, pos1, pos2, threshold=0.5):
        """Check if two positions differ significantly"""
        try:
            return any(abs(a - b) > threshold for a, b in zip(pos1, pos2))
        except:
            return True
            
    def get_next_command(self):
        """Get the next command to execute"""
        with self.data_lock:
            current_time = time.time()
            
            # Clean old points
            while (self.trajectory_buffer and 
                   current_time - self.trajectory_buffer[0]['timestamp'] > self.max_age_seconds):
                self.trajectory_buffer.popleft()
            
            # Find next unexecuted point
            for point in self.trajectory_buffer:
                if not point['executed']:
                    point['executed'] = True
                    return point['positions'], point['joint_names']
                    
            return None, None
    
    def has_pending_commands(self):
        """Check if there are pending commands"""
        with self.data_lock:
            return any(not point['executed'] for point in self.trajectory_buffer)
    
    def get_buffer_status(self):
        """Get buffer status for debugging"""
        with self.data_lock:
            total = len(self.trajectory_buffer)
            executed = sum(1 for p in self.trajectory_buffer if p['executed'])
            oldest_time = self.trajectory_buffer[0]['timestamp'] if self.trajectory_buffer else 0
            newest_time = self.trajectory_buffer[-1]['timestamp'] if self.trajectory_buffer else 0
            
            return {
                'total_points': total,
                'executed_points': executed,
                'pending_points': total - executed,
                'buffer_full': total >= self.buffer_size,
                'time_span': newest_time - oldest_time,
                'oldest_age': time.time() - oldest_time if oldest_time > 0 else 0
            }


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
        
    # Expected Lynx SES900 joint names in MoveIt (adjust if different)
    lynx_joint_names = [
        'joint_1',      # Joint 0 (Base rotation)
        'joint_2',      # Joint 1 (Shoulder)
        'joint_3',      # Joint 2 (Elbow)
        'joint_4',      # Joint 3 (Wrist 1)
        'joint_5',      # Joint 4 (Wrist 2)
        'joint_6'       # Joint 5 (Wrist 3)
    ]
    
    # Offset compensation: MoveIt home [0, -90, 0, 0, 0, 0] -> PyBullet home [0, 0, 0, 0, 0, 0]
    # So we need to add 90° to joint 1 (shoulder_lift_joint)
    joint_offsets = [0, 0, 0, 0, 0, 0]  # Degrees
    
    # Create mapping from MoveIt joint names to positions
    joint_dict = dict(zip(moveit_joint_names, moveit_positions))
    
    # Map to PyBullet order with offset compensation
    pybullet_positions = []
    for i, joint_name in enumerate(lynx_joint_names):
        if joint_name in joint_dict:
            # Apply offset compensation
            compensated_position = joint_dict[joint_name] + joint_offsets[i]
            pybullet_positions.append(compensated_position)
        else:
            print(f"[HybridROSBridge] Warning: Joint {joint_name} not found in MoveIt data")
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
    
    # Initialize HYBRID ROS bridge reader
    ros_bridge = HybridROSBridgeDataReader(
        buffer_size=30,      # Buffer 30 points (~1.5 seconds at 20Hz)
        max_age_seconds=3.0  # Keep points for max 3 seconds
    )
    ros_bridge.start_reading(update_interval=0.02)  # Read at 50Hz
    
    print("[Main] PyBullet robot initialized with HYBRID trajectory following...")
    print("[Main] Start your MoveIt planning and the robot will follow with buffered trajectory!")
    print("[Main] Buffer size: 30 points (~1.5 seconds), Max age: 3 seconds")
    
    try:
        command_count = 0
        last_buffer_status_time = time.time()
        
        while True:
            if watchdog._exception_event.is_set():
                print("\n[Main] Watchdog thread reported a critical exception. Stopping.")
                robo.enter_emergency_recovery()
                break
                
            # Get next command from buffer
            moveit_positions, moveit_joint_names = ros_bridge.get_next_command()
            
            if moveit_positions and moveit_joint_names:
                # Map MoveIt joints to PyBullet order
                pybullet_positions = map_moveit_joints_to_pybullet(
                    moveit_positions, moveit_joint_names
                )
                
                if pybullet_positions:
                    command_count += 1
                    
                    # Send command to PyBullet robot
                    print(f"[Main] Executing command #{command_count}")
                    print(f"[Main] MoveIt positions: {[f'{pos:.2f}°' for pos in moveit_positions]}")
                    print(f"[Main] PyBullet positions (with offset): {[f'{pos:.2f}°' for pos in pybullet_positions]}")
                    
                    robo.move_abs_with_speed(pybullet_positions, speed=rl_config.MAX_SPEED)
                    
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
                        
                    # Show buffer status periodically
                    if time.time() - last_buffer_status_time > 2.0:
                        status = ros_bridge.get_buffer_status()
                        print(f"[Main] Buffer Status: {status['pending_points']}/{status['total_points']} pending, "
                              f"span: {status['time_span']:.1f}s, oldest: {status['oldest_age']:.1f}s")
                        last_buffer_status_time = time.time()
                        
                    print("---")
                    
            else:
                # No commands in buffer, show status
                if ros_bridge.has_pending_commands():
                    print("[Main] Waiting for next command in buffer...")
                else:
                    print("[Main] Buffer empty, waiting for MoveIt commands...")
                    
            # Always step the simulation to keep it running
            with pybullet_api_lock:
                pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                    
            time.sleep(0.05)  # 20Hz execution rate
            
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
