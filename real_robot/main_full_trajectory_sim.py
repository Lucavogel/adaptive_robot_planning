#!/usr/bin/env python3
"""
PyBullet simulation with FULL MoveIt trajectory execution.
This version reads complete MoveIt trajectories and executes them with global interpolation.
Based on the existing main_sim_interpolated.py structure.
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

class FullTrajectoryROSBridgeReader:
    """
    ROS Bridge reader for COMPLETE MoveIt trajectories.
    """
    
    def __init__(self, data_file_path='/tmp/moveit_full_trajectory.json'):
        self.data_file_path = data_file_path
        self.latest_trajectory_data = None
        self.latest_timestamp = 0
        self.data_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        
    def start_reading(self, update_interval=0.1):
        """Start reading trajectory data from the ROS bridge in a separate thread."""
        if self.running:
            print("[FullTrajectoryROS] Already running.")
            return
            
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, 
                                             args=(update_interval,), 
                                             daemon=True)
        self.reader_thread.start()
        print(f"[FullTrajectoryROS] Started reading from {self.data_file_path}")
        
    def stop_reading(self):
        """Stop reading data."""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
        print("[FullTrajectoryROS] Reader stopped.")
        
    def _read_loop(self, update_interval):
        """Main reading loop for trajectory data."""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.running:
            try:
                if os.path.exists(self.data_file_path):
                    with open(self.data_file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Check for new trajectory data
                    timestamp = data.get('timestamp', 0.0)
                    if timestamp > self.latest_timestamp:
                        with self.data_lock:
                            self.latest_trajectory_data = data
                            self.latest_timestamp = timestamp
                        
                        waypoints = data.get('trajectory_waypoints', [])
                        print(f"[FullTrajectoryROS] 🆕 New trajectory: {len(waypoints)} waypoints")
                
                consecutive_errors = 0
                
            except (json.JSONDecodeError, FileNotFoundError):
                # These are expected when file doesn't exist or is being written
                pass
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors <= max_consecutive_errors:
                    print(f"[FullTrajectoryROS] Error reading data (attempt {consecutive_errors}): {e}")
                    
            time.sleep(update_interval)
    
    def get_latest_trajectory(self):
        """Get the latest trajectory data thread-safely."""
        with self.data_lock:
            return self.latest_trajectory_data.copy() if self.latest_trajectory_data else None

class SimFullTrajectoryInterpolator:
    """
    Handles global interpolation across entire MoveIt trajectory for simulation.
    """
    
    def __init__(self, interpolation_factor=1.5):
        self.interpolation_factor = interpolation_factor
        
    def interpolate_full_trajectory(self, waypoints, current_positions):
        """
        Takes all MoveIt waypoints and creates smooth interpolated path.
        
        Args:
            waypoints: List of waypoints from MoveIt trajectory
            current_positions: Current robot positions (degrees)
            
        Returns:
            List of smoothly interpolated positions
        """
        if not waypoints or len(waypoints) == 0:
            return []
        
        # Add current position as starting point
        start_waypoint = {
            'positions': current_positions,
            'time_from_start': 0.0,
            'waypoint_index': -1
        }
        full_waypoints = [start_waypoint] + waypoints
        
        interpolated_path = []
        
        for i in range(len(full_waypoints) - 1):
            current_waypoint = full_waypoints[i]
            next_waypoint = full_waypoints[i + 1]
            
            start_pos = current_waypoint['positions']
            end_pos = next_waypoint['positions']
            start_time = current_waypoint['time_from_start']
            end_time = next_waypoint['time_from_start']
            
            # Calculate number of interpolation steps for this segment
            time_duration = end_time - start_time
            max_joint_movement = max(abs(end_pos[j] - start_pos[j]) for j in range(len(start_pos)))
            
            # Adaptive step calculation
            num_steps = max(2, int(max_joint_movement * self.interpolation_factor / 10.0))
            num_steps = max(num_steps, int(time_duration * 10))  # At least 10 steps per second
            num_steps = min(num_steps, 30)  # Cap at 30 steps per segment for simulation
            
            # Generate smooth interpolated steps for this segment
            for step in range(num_steps):
                alpha = step / (num_steps - 1) if num_steps > 1 else 1.0
                
                # Use smooth easing function (ease-in-out)
                smooth_alpha = self._ease_in_out(alpha)
                
                # Interpolate positions
                interpolated_pos = []
                for j in range(len(start_pos)):
                    interp_angle = start_pos[j] + smooth_alpha * (end_pos[j] - start_pos[j])
                    interpolated_pos.append(interp_angle)
                
                # Interpolate time
                interpolated_time = start_time + alpha * (end_time - start_time)
                
                interpolated_step = {
                    'positions': interpolated_pos,
                    'time_from_start': interpolated_time,
                    'segment': i,
                    'step_in_segment': step,
                    'alpha': smooth_alpha
                }
                
                interpolated_path.append(interpolated_step)
        
        # Add the final waypoint
        if waypoints:
            final_waypoint = waypoints[-1].copy()
            final_waypoint['segment'] = len(waypoints) - 1
            final_waypoint['step_in_segment'] = 0
            final_waypoint['alpha'] = 1.0
            interpolated_path.append(final_waypoint)
        
        return interpolated_path
    
    def _ease_in_out(self, t):
        """Smooth easing function for natural movement."""
        return t * t * (3.0 - 2.0 * t)

class SimFullTrajectoryAnalyzer:
    """
    Analyzes full trajectory execution performance in simulation.
    """
    
    def __init__(self):
        self.trajectory_history = []
        
    def start_trajectory(self, waypoints):
        """Start tracking a new trajectory."""
        trajectory_data = {
            'start_time': time.time(),
            'waypoints': len(waypoints),
            'first_pos': waypoints[0]['positions'].copy() if waypoints else [],
            'last_pos': waypoints[-1]['positions'].copy() if waypoints else [],
            'expected_duration': waypoints[-1]['time_from_start'] if waypoints else 0.0,
            'step_times': []
        }
        
        self.trajectory_history.append(trajectory_data)
        return len(self.trajectory_history) - 1
    
    def record_step(self, trajectory_id, step_num, total_steps):
        """Record completion of an interpolation step."""
        if trajectory_id < len(self.trajectory_history):
            trajectory = self.trajectory_history[trajectory_id]
            current_time = time.time()
            trajectory['step_times'].append(current_time)
            
            if step_num % 20 == 0 or step_num == total_steps:
                elapsed = current_time - trajectory['start_time']
                progress = step_num / total_steps * 100
                print(f"    🎯 Step {step_num:3d}/{total_steps} ({progress:5.1f}%) | Elapsed: {elapsed:.1f}s")
    
    def finish_trajectory(self, trajectory_id):
        """Analyze completed trajectory."""
        if trajectory_id < len(self.trajectory_history):
            trajectory = self.trajectory_history[trajectory_id]
            end_time = time.time()
            
            total_duration = end_time - trajectory['start_time']
            expected_duration = trajectory['expected_duration']
            
            print(f"    📊 FULL TRAJECTORY ANALYSIS:")
            print(f"       Waypoints executed: {trajectory['waypoints']}")
            print(f"       Total duration: {total_duration:.2f}s")
            print(f"       Expected duration: {expected_duration:.2f}s")
            print(f"       Time ratio: {total_duration/expected_duration:.2f}x" if expected_duration > 0 else "")
            print(f"       Steps generated: {len(trajectory['step_times'])}")
            
            if total_duration > expected_duration * 1.5:
                print(f"       ⚠️  Execution slower than expected")
            elif total_duration < expected_duration * 0.8:
                print(f"       ⚡ Execution faster than expected")
            else:
                print(f"       ✅ Execution timing is good")

def map_moveit_joints_to_simulation(moveit_positions, moveit_joint_names, sim_joint_count=6):
    """
    Maps MoveIt joint positions to simulation joint order (Lynx SES900).
    Same mapping as existing simulation code.
    """
    if not moveit_positions or not moveit_joint_names:
        return None
        
    # Expected Lynx SES900 joint names in MoveIt
    lynx_joint_names = [
        'joint_1',      # Joint 0 (Base rotation)
        'joint_2',      # Joint 1 (Shoulder)
        'joint_3',      # Joint 2 (Upper arm)
        'joint_4',      # Joint 3 (Forearm)
        'joint_5',      # Joint 4 (Wrist)
        'joint_6'       # Joint 5 (End-effector rotation)
    ]
    
    # Offset compensation for simulation home position
    joint_offsets = [0, 0, 0, 0, 0, 0]  # Adjust as needed
    
    # Create mapping from MoveIt joint names to positions
    joint_dict = dict(zip(moveit_joint_names, moveit_positions))
    
    # Map to simulation order with offset compensation
    simulation_positions = []
    for i, joint_name in enumerate(lynx_joint_names):
        if joint_name in joint_dict:
            compensated_position = joint_dict[joint_name] + joint_offsets[i]
            simulation_positions.append(compensated_position)
        else:
            print(f"[Mapping] Warning: Joint {joint_name} not found in MoveIt data")
            return None
            
    return simulation_positions

if __name__ == '__main__':
    print("🚀 MoveIt FULL Trajectory Simulation Controller")
    print("📂 Reading complete trajectories from: /tmp/moveit_full_trajectory.json")
    print("🎯 Executes complete MoveIt trajectories with global interpolation")
    
    # Clear old data file to prevent immediate movement from stale data
    data_file_path = '/tmp/moveit_full_trajectory.json'
    if os.path.exists(data_file_path):
        print(f"[Main] Clearing old trajectory data file: {data_file_path}")
        try:
            os.remove(data_file_path)
        except Exception as e:
            print(f"[Main] Warning: Could not remove old data file: {e}")
    
    # Initialize PyBullet robot (using existing SimRobot)
    robo = SimRobot()
    if not robo.init_bus():
        print("[Main] Failed to open simulation. Exiting.")
        exit(1)
    robo.init_motors()

    # Get current robot position for initial sync
    initial_joint_angles = robo.get_Position()
    if initial_joint_angles:
        current_robot_positions = [angle[0] if angle[0] is not None else 0.0 for angle in initial_joint_angles]
        print(f"[Main] Initial robot position: {[f'{pos:.1f}°' for pos in current_robot_positions]}")
    else:
        current_robot_positions = [0.0] * 6
        print("[Main] Warning: Could not read initial position, assuming home position")
    
    # Initialize trajectory reader, interpolator and analyzer
    trajectory_reader = FullTrajectoryROSBridgeReader()
    interpolator = SimFullTrajectoryInterpolator(interpolation_factor=1.5)
    analyzer = SimFullTrajectoryAnalyzer()
    
    # Start reading trajectory data
    trajectory_reader.start_reading()
    
    # Startup delay to avoid processing old data
    startup_timestamp = time.time()
    print("[Main] ⏰ 3-second startup delay to avoid old data...")
    time.sleep(3.0)
    
    print("✅ Full Trajectory Simulation ready!")
    print("\n📋 Instructions:")
    print("1. Plan a trajectory in MoveIt (in another terminal)")
    print("2. The COMPLETE trajectory will be executed here with global interpolation")
    print("3. Press Ctrl+C to stop")
    print("=" * 80)
    
    last_trajectory_timestamp = startup_timestamp
    
    try:
        while True:
            # Get latest trajectory data
            trajectory_data = trajectory_reader.get_latest_trajectory()
            
            if trajectory_data:
                trajectory_timestamp = trajectory_data.get('timestamp', 0.0)
                
                # Check for new trajectory (ignore old data)
                if trajectory_timestamp > last_trajectory_timestamp:
                    last_trajectory_timestamp = trajectory_timestamp
                    
                    waypoints = trajectory_data.get('trajectory_waypoints', [])
                    if not waypoints:
                        continue
                    
                    print(f"\n🆕 NEW FULL TRAJECTORY RECEIVED")
                    print(f"   Waypoints: {len(waypoints)}")
                    print(f"   Duration: {trajectory_data.get('trajectory_duration', 0):.2f}s")
                    
                    # Show first and last positions
                    first_pos = [f"{pos:.1f}°" for pos in waypoints[0]['positions'][:6]]
                    last_pos = [f"{pos:.1f}°" for pos in waypoints[-1]['positions'][:6]]
                    print(f"   Start: {first_pos}")
                    print(f"   End:   {last_pos}")
                    
                    # Generate global interpolation
                    print("🔄 Generating global interpolation...")
                    interpolated_path = interpolator.interpolate_full_trajectory(waypoints, current_robot_positions)
                    
                    if interpolated_path:
                        print(f"📊 Generated {len(interpolated_path)} interpolated steps")
                        
                        # Start trajectory analysis
                        trajectory_id = analyzer.start_trajectory(waypoints)
                        
                        # Execute interpolated trajectory
                        start_time = time.time()
                        prev_time = 0.0
                        
                        for i, step in enumerate(interpolated_path):
                            step_positions = step['positions']
                            target_time = step.get('time_from_start', 0.0)
                            
                            # Map positions to simulation joints
                            sim_joint_names = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']
                            target_positions = map_moveit_joints_to_simulation(
                                step_positions, sim_joint_names
                            )
                            
                            if target_positions:
                                # Apply safety limits (same as existing code)
                                safe_target_positions = []
                                for j, pos in enumerate(target_positions):
                                    if j < len(rl_config.JOINT_LIMITS):
                                        clamped_pos = max(rl_config.JOINT_LIMITS[j][0], 
                                                        min(rl_config.JOINT_LIMITS[j][1], pos))
                                        safe_target_positions.append(clamped_pos)
                                    else:
                                        safe_target_positions.append(pos)
                                
                                # Send to simulation robot
                                try:
                                    # SimRobot.move_abs_with_speed expects degrees, not centi-degrees
                                    print(f"[DEBUG] Sending to robot: {[f'{pos:.1f}°' for pos in safe_target_positions[:6]]}")
                                    result = robo.move_abs_with_speed(safe_target_positions, speed=400)
                                    
                                    # Force PyBullet simulation step (important!)
                                    robo.step_simulation()
                                    
                                    # Update current position tracking
                                    current_robot_positions = safe_target_positions.copy()
                                    
                                    # Timing control
                                    time_step = target_time - prev_time
                                    time_step = max(0.05, min(time_step, 0.2))  # Clamp between 50ms and 200ms
                                    time.sleep(time_step)
                                    prev_time = target_time
                                    
                                    # Record step
                                    analyzer.record_step(trajectory_id, i + 1, len(interpolated_path))
                                    
                                except Exception as e:
                                    print(f"[Main] ❌ Error in step {i+1}: {e}")
                                    break
                        
                        # Finish trajectory analysis
                        analyzer.finish_trajectory(trajectory_id)
                        print(f"✅ Full trajectory completed!")
                        print("🔄 Waiting for next trajectory...\n")
                        print("=" * 80)
            
            # Small delay to avoid excessive file checking
            time.sleep(0.2)
            
    except KeyboardInterrupt:
        print("\n🛑 Full Trajectory Simulation stopped by user")
    
    finally:
        trajectory_reader.stop_reading()
        robo.close()
        print("✅ Cleanup complete")
