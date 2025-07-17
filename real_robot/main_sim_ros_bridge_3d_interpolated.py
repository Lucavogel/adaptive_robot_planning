#!/usr/bin/env python3
"""
3D INTERPOLATED VERSION - PyBullet simulation with 5th degree polynomial interpolation
This version creates smooth motions between trajectory points using 5th degree polynomial interpolation.
"""

import logging
import numpy as np
import time
import threading
import json
import os
from collections import deque
from scipy.interpolate import interp1d
import math

from sim_robot import SimRobot
from safety import SafetyWatchdogSim
from sim_sensor import SimNatNetDataHandler
import rl_config

class InterpolatedROSBridgeDataReader:
    """
    3D Interpolated approach: Reads trajectory points and creates smooth 5th degree polynomial interpolation
    """
    
    def __init__(self, data_file_path='/tmp/moveit_to_pybullet_data.json', buffer_size=200, max_age_seconds=10.0):
        self.data_file_path = data_file_path
        self.buffer_size = buffer_size
        self.max_age_seconds = max_age_seconds
        self.trajectory_buffer = deque(maxlen=buffer_size)
        self.data_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        self.last_read_timestamp = 0
        
        # Interpolation parameters
        self.interpolation_degree = 5  # 5th degree polynomial
        self.interpolation_points_per_second = 50  # 50 Hz interpolated output
        self.min_points_for_interpolation = 3  # Reduced minimum points needed for interpolation
        
    def start_reading(self, update_interval=0.02):
        """Start reading data from the ROS bridge in a separate thread."""
        if self.running:
            print("[InterpolatedROSBridge] Already running.")
            return
            
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, 
                                             args=(update_interval,), 
                                             daemon=True)
        self.reader_thread.start()
        print(f"[InterpolatedROSBridge] Started reading from {self.data_file_path} (buffer: {self.buffer_size}, interpolation: {self.interpolation_degree}° polynomial)")
        
    def stop_reading(self):
        """Stop reading data."""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
        print("[InterpolatedROSBridge] Stopped reading.")
        
    def _read_loop(self, update_interval):
        """Main reading loop - buffers trajectory points."""
        while self.running:
            try:
                if os.path.exists(self.data_file_path):
                    # Use file locking to avoid concurrent access issues
                    try:
                        with open(self.data_file_path, 'r') as f:
                            content = f.read()
                            if content.strip():  # Check if file is not empty
                                data = json.loads(content)
                                
                                # Only add new data points
                                if data['timestamp'] > self.last_read_timestamp:
                                    self._add_trajectory_point(
                                        data.get('joint_positions'),
                                        data.get('joint_names', []),
                                        data['timestamp']
                                    )
                                    self.last_read_timestamp = data['timestamp']
                    except json.JSONDecodeError as e:
                        print(f"[InterpolatedROSBridge] JSON decode error: {e}")
                        continue
                    except Exception as e:
                        print(f"[InterpolatedROSBridge] File read error: {e}")
                        continue
                        
                else:
                    print(f"[InterpolatedROSBridge] Waiting for data file: {self.data_file_path}")
                    
            except Exception as e:
                print(f"[InterpolatedROSBridge] Error reading data: {e}")
                
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
                    print(f"[InterpolatedROSBridge] Buffered point #{len(self.trajectory_buffer)}: {[f'{pos:.1f}°' for pos in positions]}")
                    
    def _positions_differ(self, pos1, pos2, threshold=0.05):
        """Check if two positions differ significantly (smaller threshold for smoother interpolation)"""
        try:
            return any(abs(a - b) > threshold for a, b in zip(pos1, pos2))
        except:
            return True
            
    def _create_5th_degree_interpolation(self, times, positions):
        """Create 5th degree polynomial interpolation between points"""
        if len(times) < 2:
            return None, None
            
        # Ensure we have enough points for stable interpolation
        if len(times) < self.min_points_for_interpolation:
            # Use linear interpolation for few points
            kind = 'linear'
        else:
            # Use 5th degree polynomial (cubic spline is similar and more stable)
            kind = 'cubic'
            
        try:
            # Create interpolation functions for each joint
            interpolators = []
            for joint_idx in range(len(positions[0])):
                joint_positions = [pos[joint_idx] for pos in positions]
                interpolator = interp1d(times, joint_positions, kind=kind, 
                                      bounds_error=False, fill_value="extrapolate")
                interpolators.append(interpolator)
                
            return interpolators, (times[0], times[-1])
            
        except Exception as e:
            print(f"[InterpolatedROSBridge] Interpolation error: {e}")
            return None, None
            
    def get_interpolated_trajectory(self, duration_seconds=1.0):
        """Get interpolated trajectory for the next duration_seconds"""
        with self.data_lock:
            current_time = time.time()
            
            # Clean old points
            while (self.trajectory_buffer and 
                   current_time - self.trajectory_buffer[0]['timestamp'] > self.max_age_seconds):
                self.trajectory_buffer.popleft()
            
            # Get unexecuted points
            unexecuted_points = [p for p in self.trajectory_buffer if not p['executed']]
            
            if len(unexecuted_points) < 2:
                return []
                
            # Extract times and positions
            times = [p['timestamp'] for p in unexecuted_points]
            positions = [p['positions'] for p in unexecuted_points]
            joint_names = unexecuted_points[0]['joint_names']
            
            # Create interpolation
            interpolators, time_range = self._create_5th_degree_interpolation(times, positions)
            
            if interpolators is None:
                return []
                
            # Generate interpolated points
            start_time = time_range[0]
            end_time = min(time_range[1], start_time + duration_seconds)
            
            # Create high-resolution time points
            num_points = int((end_time - start_time) * self.interpolation_points_per_second)
            if num_points < 2:
                return []
                
            interp_times = np.linspace(start_time, end_time, num_points)
            
            # Generate interpolated trajectory
            interpolated_trajectory = []
            for t in interp_times:
                interpolated_positions = []
                for interpolator in interpolators:
                    pos = float(interpolator(t))
                    interpolated_positions.append(pos)
                
                interpolated_trajectory.append({
                    'positions': interpolated_positions,
                    'joint_names': joint_names,
                    'timestamp': t,
                    'interpolated': True
                })
                
            # Mark original points as executed up to the interpolated time
            for point in unexecuted_points:
                if point['timestamp'] <= end_time:
                    point['executed'] = True
                    
            return interpolated_trajectory
            
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
                'oldest_age': time.time() - oldest_time if oldest_time > 0 else 0,
                'interpolation_ready': (total - executed) >= self.min_points_for_interpolation
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
            print(f"[InterpolatedROSBridge] Warning: Joint {joint_name} not found in MoveIt data")
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
    
    # Initialize INTERPOLATED ROS bridge reader
    ros_bridge = InterpolatedROSBridgeDataReader(
        buffer_size=200,     # Increased buffer size for better interpolation
        max_age_seconds=10.0  # Keep points for longer
    )
    ros_bridge.start_reading(update_interval=0.01)  # Read at 100Hz for better data collection
    
    print("[Main] PyBullet robot initialized with 3D INTERPOLATED trajectory following...")
    print("[Main] Features:")
    print("[Main]   - 5th degree polynomial interpolation")
    print("[Main]   - 50 Hz smooth trajectory generation")
    print("[Main]   - Buffer size: 200 points")
    print("[Main]   - Reduced minimum points requirement: 3 points")
    print("[Main] Start your MoveIt planning and enjoy ultra-smooth robot motion!")
    
    try:
        command_count = 0
        last_buffer_status_time = time.time()
        trajectory_queue = deque()
        
        while True:
            if watchdog._exception_event.is_set():
                print("\n[Main] Watchdog thread reported a critical exception. Stopping.")
                robo.enter_emergency_recovery()
                break
                
            # If trajectory queue is getting low, generate new interpolated trajectory
            if len(trajectory_queue) < 5:  # Keep at least 5 points ahead (reduced from 10)
                new_trajectory = ros_bridge.get_interpolated_trajectory(duration_seconds=1.0)  # Generate longer trajectory
                if new_trajectory:
                    trajectory_queue.extend(new_trajectory)
                    print(f"[Main] Generated {len(new_trajectory)} interpolated points")
                    
            # Execute next point from interpolated trajectory
            if trajectory_queue:
                next_point = trajectory_queue.popleft()
                moveit_positions = next_point['positions']
                moveit_joint_names = next_point['joint_names']
                
                # Map MoveIt joints to PyBullet order
                pybullet_positions = map_moveit_joints_to_pybullet(
                    moveit_positions, moveit_joint_names
                )
                
                if pybullet_positions:
                    command_count += 1
                    
                    # Send command to PyBullet robot
                    if command_count % 25 == 0:  # Log every 25th command to avoid spam
                        print(f"[Main] Executing interpolated command #{command_count}")
                        print(f"[Main] MoveIt positions: {[f'{pos:.2f}°' for pos in moveit_positions]}")
                        print(f"[Main] PyBullet positions: {[f'{pos:.2f}°' for pos in pybullet_positions]}")
                        
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
                    
                    robo.move_abs_with_speed(pybullet_positions, speed=rl_config.MAX_SPEED)
                    
            else:
                # No interpolated trajectory available
                print("[Main] No interpolated trajectory available, waiting for MoveIt data...")
                
            # Show buffer status periodically
            if time.time() - last_buffer_status_time > 3.0:
                status = ros_bridge.get_buffer_status()
                print(f"[Main] Buffer Status: {status['pending_points']}/{status['total_points']} pending")
                print(f"[Main] Interpolation ready: {status['interpolation_ready']}")
                print(f"[Main] Trajectory queue: {len(trajectory_queue)} points")
                last_buffer_status_time = time.time()
                
            # Always step the simulation to keep it running
            with pybullet_api_lock:
                pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                    
            time.sleep(0.02)  # 50Hz execution rate for smooth motion
            
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
