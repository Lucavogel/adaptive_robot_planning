#!/usr/bin/env python3
"""
Real robot controller with FULL TRAJECTORY execution from MoveIt.
This script reads the complete planned trajectory and executes it smoothly with global interpolation.
"""

import logging
import numpy as np
import time
import threading
import json
import os
import math

from robot import Robot
from safety import SafetyWatchdog
import rl_config

class TrajectoryReader:
    """
    Reads complete MoveIt trajectories from the ROS bridge.
    """
    
    def __init__(self, data_file_path='/tmp/moveit_full_trajectory.json'):
        self.data_file_path = data_file_path
        self.latest_trajectory = None
        self.latest_timestamp = 0
        self.data_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        
    def start_reading(self, update_interval=0.1):
        """Start reading trajectory data from the ROS bridge."""
        if self.running:
            print("[TrajectoryReader] Already running.")
            return
            
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, 
                                             args=(update_interval,), 
                                             daemon=True)
        self.reader_thread.start()
        print(f"[TrajectoryReader] Started reading from {self.data_file_path}")
        
    def stop_reading(self):
        """Stop reading data."""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
        print("[TrajectoryReader] Stopped reading.")
        
    def _read_loop(self, update_interval):
        """Main reading loop."""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            try:
                if os.path.exists(self.data_file_path):
                    with open(self.data_file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Only process data if bridge is ready
                    if not data.get('bridge_ready', False):
                        if consecutive_errors == 0:
                            print(f"[TrajectoryReader] Bridge not ready yet, waiting...")
                        consecutive_errors += 1
                        time.sleep(update_interval)
                        continue
                        
                    # Check if trajectory is newer
                    if data['timestamp'] > self.latest_timestamp:
                        with self.data_lock:
                            self.latest_trajectory = data
                            self.latest_timestamp = data['timestamp']
                            
                        print(f"[TrajectoryReader] 🎯 New trajectory: {data['total_waypoints']} waypoints, "
                              f"duration: {data['trajectory_duration']:.2f}s")
                    
                    consecutive_errors = 0
                            
                else:
                    if consecutive_errors == 0:
                        print(f"[TrajectoryReader] Waiting for trajectory file: {self.data_file_path}")
                    consecutive_errors += 1
                    
            except json.JSONDecodeError as e:
                consecutive_errors += 1
                if consecutive_errors <= max_consecutive_errors:
                    print(f"[TrajectoryReader] JSON decode error: {e}")
                else:
                    consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors <= max_consecutive_errors:
                    print(f"[TrajectoryReader] Error reading trajectory: {e}")
                    
            time.sleep(update_interval)
            
    def get_latest_trajectory(self):
        """Get the latest complete trajectory."""
        with self.data_lock:
            return self.latest_trajectory.copy() if self.latest_trajectory else None

class GlobalTrajectoryInterpolator:
    """
    Performs global interpolation on complete MoveIt trajectories for smooth real robot execution.
    """
    
    def __init__(self, interpolation_density=0.1, min_step_time=0.15, max_speed=1300):
        self.interpolation_density = interpolation_density  # seconds between interpolated points
        self.min_step_time = min_step_time  # minimum time between robot commands
        self.max_speed = max_speed
        
    def interpolate_trajectory(self, trajectory_waypoints):
        """
        Perform global interpolation on the complete trajectory.
        
        Args:
            trajectory_waypoints: List of waypoints from MoveIt
            
        Returns:
            List of smoothly interpolated positions with timing
        """
        if not trajectory_waypoints or len(trajectory_waypoints) < 2:
            return trajectory_waypoints
        
        print(f"[GlobalInterpolator] Processing trajectory with {len(trajectory_waypoints)} waypoints")
        
        # Extract positions and times
        positions = [wp['positions'] for wp in trajectory_waypoints]
        times = [wp['time_from_start'] for wp in trajectory_waypoints]
        
        # If no timing info, create uniform timing
        if all(t == 0.0 for t in times):
            total_distance = self._calculate_trajectory_distance(positions)
            estimated_duration = total_distance / 30.0  # Estimate 30°/s average speed
            times = [i * estimated_duration / (len(positions) - 1) for i in range(len(positions))]
            print(f"[GlobalInterpolator] No timing info, estimated duration: {estimated_duration:.2f}s")
        
        # Create interpolated timeline
        total_duration = times[-1]
        num_interpolated_steps = max(int(total_duration / self.interpolation_density), len(positions))
        
        # Ensure minimum time between steps for real robot safety
        actual_step_time = max(total_duration / num_interpolated_steps, self.min_step_time)
        num_interpolated_steps = int(total_duration / actual_step_time)
        
        interpolated_positions = []
        interpolated_times = []
        
        for i in range(num_interpolated_steps + 1):
            target_time = i * actual_step_time
            
            # Find surrounding waypoints
            if target_time >= times[-1]:
                # Use last waypoint
                interp_pos = positions[-1].copy()
            else:
                # Find the two waypoints to interpolate between
                for j in range(len(times) - 1):
                    if times[j] <= target_time <= times[j + 1]:
                        # Linear interpolation between waypoints j and j+1
                        dt = times[j + 1] - times[j]
                        if dt > 0:
                            alpha = (target_time - times[j]) / dt
                            # Apply smooth easing for real robot
                            alpha = self._smooth_easing(alpha)
                            
                            interp_pos = []
                            for k in range(len(positions[j])):
                                val = positions[j][k] + alpha * (positions[j + 1][k] - positions[j][k])
                                interp_pos.append(val)
                        else:
                            interp_pos = positions[j].copy()
                        break
                else:
                    # Fallback to first position
                    interp_pos = positions[0].copy()
            
            interpolated_positions.append(interp_pos)
            interpolated_times.append(target_time)
        
        print(f"[GlobalInterpolator] Generated {len(interpolated_positions)} smooth steps "
              f"(step time: {actual_step_time:.3f}s)")
        
        # Create interpolated waypoints
        interpolated_waypoints = []
        for i, (pos, t) in enumerate(zip(interpolated_positions, interpolated_times)):
            waypoint = {
                'positions': pos,
                'time_from_start': t,
                'step_index': i,
                'is_interpolated': True
            }
            interpolated_waypoints.append(waypoint)
        
        return interpolated_waypoints
    
    def _smooth_easing(self, t):
        """Apply smooth easing function for real robot movements."""
        # Smooth S-curve (ease-in-out cubic)
        return 3 * t * t - 2 * t * t * t
    
    def _calculate_trajectory_distance(self, positions):
        """Calculate total distance of trajectory in degrees."""
        total_distance = 0.0
        for i in range(1, len(positions)):
            step_distance = sum(abs(positions[i][j] - positions[i-1][j]) 
                              for j in range(len(positions[i])))
            total_distance += step_distance
        return total_distance
    
    def calculate_step_speed(self, current_pos, next_pos, time_delta):
        """Calculate appropriate speed for trajectory step."""
        if time_delta <= 0:
            return self.max_speed
        
        # Calculate maximum joint movement
        max_movement = max(abs(next_pos[i] - current_pos[i]) for i in range(len(current_pos)))
        
        # Calculate required speed based on movement and time
        required_speed = max_movement / time_delta * 60  # Convert to speed units
        
        # Clamp to safe range (500-1300 work well for this robot)
        safe_speed = max(500, min(self.max_speed, int(required_speed)))
        
        return safe_speed

class TrajectoryExecutor:
    """
    Executes interpolated trajectories on the real robot.
    """
    
    def __init__(self, robot, safety_limits):
        self.robot = robot
        self.safety_limits = safety_limits
        self.execution_stats = {
            'trajectories_executed': 0,
            'total_waypoints_executed': 0,
            'total_execution_time': 0.0
        }
    
    def execute_trajectory(self, interpolated_waypoints):
        """Execute the complete interpolated trajectory on real robot."""
        if not interpolated_waypoints:
            print("[TrajectoryExecutor] No waypoints to execute")
            return False
        
        print(f"[TrajectoryExecutor] 🚀 Executing trajectory with {len(interpolated_waypoints)} steps")
        
        start_time = time.time()
        successful_steps = 0
        
        # Get starting position
        current_robot_pos = self.robot.get_Position()
        if current_robot_pos:
            current_pos = [angle[0] if angle[0] is not None else 0.0 for angle in current_robot_pos]
            print(f"[TrajectoryExecutor] Starting from: {[f'{pos:.1f}°' for pos in current_pos]}")
        else:
            print("[TrajectoryExecutor] ⚠️ Could not read starting position")
            current_pos = [0.0] * 6
        
        # Execute each waypoint
        for i, waypoint in enumerate(interpolated_waypoints):
            target_pos = waypoint['positions']
            
            # Apply safety limits
            safe_pos = self._apply_safety_limits(target_pos)
            
            # Calculate time to next waypoint
            if i < len(interpolated_waypoints) - 1:
                time_delta = interpolated_waypoints[i + 1]['time_from_start'] - waypoint['time_from_start']
            else:
                time_delta = 0.15  # Default time for last waypoint
            
            # Calculate appropriate speed
            interpolator = GlobalTrajectoryInterpolator()
            speed = interpolator.calculate_step_speed(current_pos, safe_pos, time_delta)
            
            print(f"[TrajectoryExecutor] Step {i+1}/{len(interpolated_waypoints)}: "
                  f"{[f'{pos:.1f}°' for pos in safe_pos]} (speed: {speed}, Δt: {time_delta:.3f}s)")
            
            try:
                # Send command to robot
                result = self.robot.move_abs_with_speed(safe_pos, speed=speed)
                
                if result:
                    successful_steps += 1
                    current_pos = safe_pos.copy()
                    
                    # Wait for step completion
                    time.sleep(max(0.15, time_delta))
                else:
                    print(f"[TrajectoryExecutor] ❌ Command failed at step {i+1}")
                    break
                    
            except Exception as e:
                print(f"[TrajectoryExecutor] ❌ Error at step {i+1}: {e}")
                break
        
        # Execution summary
        total_time = time.time() - start_time
        success_rate = successful_steps / len(interpolated_waypoints) * 100
        
        print(f"[TrajectoryExecutor] 📊 EXECUTION COMPLETE:")
        print(f"  ✅ Steps completed: {successful_steps}/{len(interpolated_waypoints)} ({success_rate:.1f}%)")
        print(f"  ⏱️ Total time: {total_time:.2f}s")
        print(f"  🚀 Average step rate: {successful_steps/total_time:.1f} steps/s")
        
        # Update stats
        self.execution_stats['trajectories_executed'] += 1
        self.execution_stats['total_waypoints_executed'] += successful_steps
        self.execution_stats['total_execution_time'] += total_time
        
        return successful_steps == len(interpolated_waypoints)
    
    def _apply_safety_limits(self, positions):
        """Apply joint safety limits to positions."""
        safe_positions = []
        for i, pos in enumerate(positions):
            if i < len(self.safety_limits):
                min_limit, max_limit = self.safety_limits[i]
                safe_pos = np.clip(pos, min_limit, max_limit)
                safe_positions.append(float(safe_pos))
                
                if abs(safe_pos - pos) > 0.1:
                    print(f"[Safety] Joint {i} clamped from {pos:.1f}° to {safe_pos:.1f}°")
            else:
                safe_positions.append(float(pos))
        
        return safe_positions
    
    def get_stats(self):
        """Get execution statistics."""
        return self.execution_stats.copy()

if __name__ == '__main__':
    # Initialize real robot
    robo = Robot(portname=rl_config.PORT)
    if not robo.init_bus():
        print("[Main] Failed to open serial port. Exiting.")
        exit(1)
    robo.init_motors()

    # Initialize safety watchdog
    watchdog = SafetyWatchdog(
        robot_controller=robo,
        natnet_data_handler=None,
        joint_limits=rl_config.JOINT_LIMITS,
        marker_radii=rl_config.MARKER_RADII,
    )
    robo.joint_watchdog = watchdog
    watchdog.start(check_interval=rl_config.WATCHDOG_INTERVAL)
    
    # Initialize trajectory reader
    trajectory_reader = TrajectoryReader()
    trajectory_reader.start_reading(update_interval=0.1)
    
    # Initialize global interpolator
    interpolator = GlobalTrajectoryInterpolator(
        interpolation_density=0.1,  # 100ms between interpolated points
        min_step_time=0.15,         # Minimum 150ms between robot commands
        max_speed=rl_config.MAX_SPEED
    )
    
    # Initialize trajectory executor
    executor = TrajectoryExecutor(robo, rl_config.JOINT_LIMITS)
    
    print("[Main] 🎯 FULL TRAJECTORY robot controller initialized...")
    print("[Main] Features:")
    print("  - Reads COMPLETE MoveIt trajectories (not just goals)")
    print("  - Global interpolation over entire planned path")
    print("  - Smooth execution with timing preservation")
    print("  - Real-time trajectory processing")
    print("[Main] Start MoveIt planning and watch SMOOTH trajectory execution!")
    
    print("\n" + "="*70)
    print("🎬 TRAJECTORY MODE: Waiting for complete MoveIt trajectories...")
    print("   ✅ Will execute full planned paths smoothly")
    print("   🎯 Each MoveIt plan becomes one smooth robot movement")
    print("   ⚠️  Make sure MoveIt trajectory bridge is running!")
    print("="*70)
    
    try:
        last_trajectory_timestamp = 0
        trajectory_count = 0
        
        while True:
            if watchdog._exception_event.is_set():
                print("\n[Main] Watchdog reported critical exception. Stopping.")
                robo.enter_emergency_recovery()
                break
            
            # Get latest complete trajectory
            trajectory_data = trajectory_reader.get_latest_trajectory()
            
            if trajectory_data and trajectory_data['timestamp'] > last_trajectory_timestamp:
                trajectory_count += 1
                last_trajectory_timestamp = trajectory_data['timestamp']
                
                waypoints = trajectory_data['trajectory_waypoints']
                print(f"\n[Main] 🎬 TRAJECTORY #{trajectory_count} RECEIVED!")
                print(f"[Main] Waypoints: {len(waypoints)}")
                print(f"[Main] Duration: {trajectory_data['trajectory_duration']:.2f}s")
                
                if len(waypoints) >= 2:
                    # Show start and end positions
                    start_pos = [f"{pos:.1f}°" for pos in waypoints[0]['positions']]
                    end_pos = [f"{pos:.1f}°" for pos in waypoints[-1]['positions']]
                    print(f"[Main] From: {start_pos}")
                    print(f"[Main] To:   {end_pos}")
                    
                    # Perform global interpolation
                    print(f"[Main] 🔄 Performing global interpolation...")
                    interpolated_waypoints = interpolator.interpolate_trajectory(waypoints)
                    
                    # Execute the smooth trajectory
                    print(f"[Main] 🚀 Executing smooth trajectory...")
                    success = executor.execute_trajectory(interpolated_waypoints)
                    
                    if success:
                        print(f"[Main] ✅ Trajectory #{trajectory_count} completed successfully!")
                    else:
                        print(f"[Main] ❌ Trajectory #{trajectory_count} failed during execution")
                    
                    # Show execution statistics
                    stats = executor.get_stats()
                    print(f"[Main] 📊 Total executed: {stats['trajectories_executed']} trajectories, "
                          f"{stats['total_waypoints_executed']} waypoints")
                    
                    print("="*70)
                else:
                    print("[Main] ⚠️ Trajectory too short (< 2 waypoints)")
            
            time.sleep(0.2)  # 5Hz check rate
            
    except KeyboardInterrupt:
        print("\n[Main] CTRL-C detected. Shutting down...")
        robo.enter_emergency_recovery()
    except Exception as e:
        print(f"[Main] Exception in main loop: {e}")
        robo.enter_emergency_recovery()
    finally:
        print("[Main] Cleaning up...")
        trajectory_reader.stop_reading()
        watchdog.stop()
        robo.shutdown()
        print("[Main] Shutdown complete.")
