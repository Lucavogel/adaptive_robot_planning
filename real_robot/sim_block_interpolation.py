#!/usr/bin/env python3
"""
PyBullet simulation with smooth interpolation between MoveIt commands.
This version interpolates between current position and target position for smoother movement.
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

class InterpolatedROSBridgeReader:
    """
    ROS Bridge reader with interpolation capabilities for smooth movement.
    """
    
    def __init__(self, data_file_path='/tmp/moveit_to_pybullet_data.json'):
        self.data_file_path = data_file_path
        self.latest_joint_positions = None
        self.latest_joint_names = []
        self.latest_timestamp = 0
        self.data_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        
    def start_reading(self, update_interval=0.05):
        """Start reading data from the ROS bridge in a separate thread."""
        if self.running:
            print("[InterpolatedROSBridge] Already running.")
            return
            
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, 
                                             args=(update_interval,), 
                                             daemon=True)
        self.reader_thread.start()
        print(f"[InterpolatedROSBridge] Started reading from {self.data_file_path}")
        
    def stop_reading(self):
        """Stop reading data."""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)
        print("[InterpolatedROSBridge] Stopped reading.")
        
    def _read_loop(self, update_interval):
        """Main reading loop."""
        consecutive_errors = 0
        max_consecutive_errors = 5
        startup_delay = 2.0  # Wait 2 seconds before processing commands
        startup_time = time.time()
        
        while self.running:
            try:
                # Skip processing during startup delay
                if time.time() - startup_time < startup_delay:
                    time.sleep(0.5)
                    continue
                    
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
                            # Only log if positions actually changed significantly
                            if self._positions_changed(self.latest_joint_positions):
                                print(f"[InterpolatedROSBridge] New target: {[f'{pos:.1f}°' for pos in self.latest_joint_positions]}")
                    
                    # Reset error counter on successful read
                    consecutive_errors = 0
                            
                else:
                    if consecutive_errors == 0:  # Only log first time
                        print(f"[InterpolatedROSBridge] Waiting for data file: {self.data_file_path}")
                    consecutive_errors += 1
                    
            except json.JSONDecodeError as e:
                consecutive_errors += 1
                if consecutive_errors <= max_consecutive_errors:
                    print(f"[InterpolatedROSBridge] JSON decode error (attempt {consecutive_errors}): {e}")
                    time.sleep(0.1)  # Wait longer before retry
                    continue
                else:
                    print(f"[InterpolatedROSBridge] Too many consecutive JSON errors, continuing...")
                    consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                if consecutive_errors <= max_consecutive_errors:
                    print(f"[InterpolatedROSBridge] Error reading data (attempt {consecutive_errors}): {e}")
                    
            time.sleep(update_interval)
    
    def _positions_changed(self, new_positions, threshold=1.0):
        """Check if positions changed significantly."""
        if not hasattr(self, '_last_logged_positions') or not self._last_logged_positions:
            self._last_logged_positions = new_positions.copy()
            return True
        
        try:
            changed = any(abs(a - b) > threshold for a, b in zip(new_positions, self._last_logged_positions))
            if changed:
                self._last_logged_positions = new_positions.copy()
            return changed
        except:
            return True
            
    def get_latest_joint_positions(self):
        """Get the latest joint positions thread-safely."""
        with self.data_lock:
            return self.latest_joint_positions.copy() if self.latest_joint_positions else None
            
    def get_joint_names(self):
        """Get the joint names."""
        with self.data_lock:
            return self.latest_joint_names.copy()

class SimRobotInterpolator:
    """
    Handles smooth interpolation for simulation robot with same logic as real robot.
    """
    
    def __init__(self, interpolation_steps=6, position_tolerance=1.0, max_step_speed=300):
        self.interpolation_steps = interpolation_steps
        self.position_tolerance = position_tolerance  # degrees
        self.max_step_speed = max_step_speed  # Simulation speed units
        
    def interpolate_to_target(self, current_positions, target_positions, steps=None):
        """
        Generate interpolated positions from current to target for simulation robot.
        Uses same logic as real robot for consistency.
        
        Args:
            current_positions: List of current joint positions (degrees)
            target_positions: List of target joint positions (degrees)
            steps: Number of interpolation steps (default: adaptive)
            
        Returns:
            List of interpolated position arrays
        """
        if current_positions is None or target_positions is None:
            return [target_positions] if target_positions else []
            
        # Calculate maximum movement to adapt number of steps
        max_movement = max(abs(target_positions[i] - current_positions[i]) 
                          for i in range(len(target_positions)))
        
        # Adapt steps based on movement size (same as real robot)
        if max_movement < 3.0:
            steps = 2  # Very small movements: minimal steps
        elif max_movement < 10.0:
            steps = 3  # Small movements: few steps
        elif max_movement < 30.0:
            steps = 5  # Medium movements: moderate steps
        elif max_movement < 60.0:
            steps = 8  # Large movements: many steps
        else:
            steps = 10  # Very large movements: maximum steps
        
        interpolated_positions = []
        
        for step in range(1, steps + 1):
            alpha = step / steps
            # Use smooth easing function (ease-in-out same as real robot)
            alpha = 3 * alpha ** 2 - 2 * alpha ** 3
            
            interp_pos = []
            for i in range(len(target_positions)):
                interp_val = current_positions[i] + alpha * (target_positions[i] - current_positions[i])
                interp_pos.append(interp_val)
                
            interpolated_positions.append(interp_pos)
            
        print(f"[SimRobotInterpolator] Generated {len(interpolated_positions)} steps for max movement {max_movement:.1f}°")
        return interpolated_positions
    
    def needs_interpolation(self, current_positions, target_positions):
        """Check if interpolation is needed based on position difference."""
        if current_positions is None or target_positions is None:
            return True
            
        max_diff = max(abs(target_positions[i] - current_positions[i]) 
                      for i in range(len(target_positions)))
        return max_diff > self.position_tolerance
    
    def calculate_step_speed(self, current_positions, target_positions, step_positions):
        """Calculate appropriate speed for this interpolation step (simulation)."""
        # Calculate step distance
        step_distances = [abs(step_positions[i] - current_positions[i]) 
                         for i in range(len(step_positions))]
        max_step_distance = max(step_distances)
        
        # Adapt speed based on step size (same logic as real robot)
        if max_step_distance < 2.0:
            return min(self.max_step_speed * 0.4, 200)  # Very slow for precision
        elif max_step_distance < 5.0:
            return min(self.max_step_speed * 0.6, 300)  # Moderate speed
        elif max_step_distance < 15.0:
            return min(self.max_step_speed * 0.8, 400)  # Normal speed
        else:
            return self.max_step_speed  # Full speed for large steps


class SimRobotMovementAnalyzer:
    """
    Analyzes simulation robot movement performance and provides metrics.
    """
    
    def __init__(self):
        self.movement_history = []
        
    def start_movement(self, current_pos, target_pos, num_steps):
        """Start tracking a new movement."""
        movement_data = {
            'start_time': time.time(),
            'start_pos': current_pos.copy(),
            'target_pos': target_pos.copy(),
            'num_steps': num_steps,
            'max_distance': max(abs(target_pos[i] - current_pos[i]) for i in range(len(target_pos))),
            'step_times': [],
            'step_speeds': []
        }
        
        self.movement_history.append(movement_data)
        return len(self.movement_history) - 1
    
    def record_step(self, movement_id, step_num, step_speed):
        """Record completion of an interpolation step."""
        if movement_id < len(self.movement_history):
            movement = self.movement_history[movement_id]
            current_time = time.time()
            movement['step_times'].append(current_time)
            movement['step_speeds'].append(step_speed)
            
            if step_num == 1:
                step_duration = current_time - movement['start_time']
            else:
                step_duration = current_time - movement['step_times'][-2]
                
            print(f"    ⏱️  Step {step_num} took {step_duration*1000:.0f}ms (speed: {step_speed})")
    
    def finish_movement(self, movement_id):
        """Analyze completed movement."""
        if movement_id < len(self.movement_history):
            movement = self.movement_history[movement_id]
            end_time = time.time()
            
            total_duration = end_time - movement['start_time']
            avg_step_time = total_duration / movement['num_steps'] * 1000
            avg_speed = movement['max_distance'] / total_duration if total_duration > 0 else 0
            
            print(f"    📊 SIMULATION MOVEMENT ANALYSIS:")
            print(f"       Total duration: {total_duration*1000:.0f}ms")
            print(f"       Average step time: {avg_step_time:.0f}ms")
            print(f"       Max joint movement: {movement['max_distance']:.2f}°")
            print(f"       Average speed: {avg_speed:.1f}°/s")
            print(f"       Steps used: {movement['num_steps']}")
            
            # Performance assessment for simulation
            if avg_step_time > 120:
                print(f"       ⚠️  Movement is slow (simulation)")
            elif avg_step_time < 30:
                print(f"       ⚡ Movement is fast (simulation)")
            else:
                print(f"       ✅ Movement timing is good")


def map_moveit_joints_to_simulation(moveit_positions, moveit_joint_names, sim_joint_count=6):
    """
    Maps MoveIt joint positions to simulation joint order (Lynx SES900) with offset compensation.
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
    
    # Offset compensation for simulation home position (same as real robot)
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
    # Clear old data file to prevent immediate movement from stale data
    data_file_path = '/tmp/moveit_to_pybullet_data.json'
    if os.path.exists(data_file_path):
        print(f"[Main] Clearing old MoveIt data file: {data_file_path}")
        try:
            os.remove(data_file_path)
        except Exception as e:
            print(f"[Main] Warning: Could not remove old data file: {e}")
    
    # Initialize PyBullet robot
    robo = SimRobot()
    if not robo.init_bus():
        print("[Main] Failed to open simulation. Exiting.")
        exit(1)
    robo.init_motors()

    # Get current robot position for initial sync
    initial_joint_angles = robo.get_Position()
    if initial_joint_angles:
        initial_positions = [angle[0] if angle[0] is not None else 0.0 for angle in initial_joint_angles]
        print(f"[Main] Initial robot position: {[f'{pos:.1f}°' for pos in initial_positions]}")
    else:
        initial_positions = [0.0] * 6
        print("[Main] Warning: Could not read initial position, assuming home position")
    
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
    
    # Initialize interpolated ROS bridge reader
    ros_bridge = InterpolatedROSBridgeReader()
    ros_bridge.start_reading(update_interval=0.05)  # Read at 20Hz
    
    # Initialize interpolator for simulation
    interpolator = SimRobotInterpolator(
        interpolation_steps=6,     # Base number of steps (same as real robot)
        position_tolerance=1.0,    # Larger tolerance for consistency  
        max_step_speed=400         # Conservative max speed for simulation
    )
    
    # Initialize movement analyzer
    analyzer = SimRobotMovementAnalyzer()
    
    # Initialize movement analyzer (duplicate removed later)
    
    print("[Main] PyBullet robot initialized with SMOOTH INTERPOLATION...")
    print("[Main] Features:")
    print("  - Conservative interpolation (2-10 steps based on movement)")
    print("  - Adaptive speed control per step")
    print("  - Safety-focused timing")
    print("  - Position tolerance: 1.0°")
    print("  - Initial startup delay: 2.0s (prevents immediate large movements)")
    print("[Main] Start your MoveIt planning and watch smooth simulation movement!")
    print("[Main] Robot will wait 2 seconds before processing MoveIt commands...")
    
    try:
        command_count = 0
        last_moveit_positions = None
        current_robot_positions = None  # Track current position for interpolation
        
        while True:
            if watchdog._exception_event.is_set():
                print("\n[Main] Watchdog thread reported a critical exception. Stopping.")
                robo.enter_emergency_recovery()
                break
                
            # Get latest joint positions from ROS bridge
            moveit_positions = ros_bridge.get_latest_joint_positions()
            moveit_joint_names = ros_bridge.get_joint_names()
            
            if moveit_positions and moveit_joint_names:
                # Check if positions have changed
                if last_moveit_positions is None or moveit_positions != last_moveit_positions:
                    # Map MoveIt joints to simulation order
                    target_positions = map_moveit_joints_to_simulation(
                        moveit_positions, moveit_joint_names
                    )
                    
                    if target_positions:
                        command_count += 1
                        
                        # Get current robot position if we don't have it
                        if current_robot_positions is None:
                            current_joint_angles = robo.get_Position()
                            if current_joint_angles:
                                current_robot_positions = [angle[0] if angle[0] is not None else 0.0 
                                                         for angle in current_joint_angles]
                        
                        print(f"\n[Main] ===== SMOOTH MOVEMENT #{command_count} =====")
                        print(f"[Main] MoveIt target: {[f'{pos:.2f}°' for pos in moveit_positions]}")
                        print(f"[Main] Simulation target: {[f'{pos:.2f}°' for pos in target_positions]}")
                        
                        # Apply safety limits before interpolation
                        safe_target_positions = []
                        for j, angle in enumerate(target_positions):
                            if j < len(rl_config.JOINT_LIMITS):
                                min_limit, max_limit = rl_config.JOINT_LIMITS[j]
                                clamped_angle = np.clip(angle, min_limit, max_limit)
                                safe_target_positions.append(float(clamped_angle))
                                
                                if abs(clamped_angle - angle) > 0.1:
                                    print(f"[Main] ⚠️  Joint {j} clamped from {angle:.1f}° to {clamped_angle:.1f}°")
                            else:
                                safe_target_positions.append(float(angle))
                        
                        # Check if interpolation is needed
                        if interpolator.needs_interpolation(current_robot_positions, safe_target_positions):
                            # Generate interpolated path
                            interpolated_steps = interpolator.interpolate_to_target(
                                current_robot_positions, safe_target_positions
                            )
                            
                            print(f"[Main] Executing {len(interpolated_steps)} interpolated steps...")
                            
                            # Start movement tracking
                            movement_id = analyzer.start_movement(
                                current_robot_positions, safe_target_positions, len(interpolated_steps)
                            )
                            
                            # Execute each interpolation step
                            for i, step_positions in enumerate(interpolated_steps):
                                print(f"[Main] Step {i+1}/{len(interpolated_steps)}: {[f'{pos:.1f}°' for pos in step_positions]}")
                                
                                # Calculate appropriate speed for this step
                                step_speed = interpolator.calculate_step_speed(
                                    current_robot_positions, safe_target_positions, step_positions
                                )
                                
                                # Apply safety limits to step positions
                                safe_step_positions = []
                                for j, angle in enumerate(step_positions):
                                    if j < len(rl_config.JOINT_LIMITS):
                                        min_limit, max_limit = rl_config.JOINT_LIMITS[j]
                                        clamped_angle = np.clip(angle, min_limit, max_limit)
                                        safe_step_positions.append(float(clamped_angle))
                                    else:
                                        safe_step_positions.append(float(angle))
                                
                                # Send command to simulation robot
                                try:
                                    robo.move_abs_with_speed(safe_step_positions, speed=step_speed)
                                    
                                    # Record step completion
                                    analyzer.record_step(movement_id, i+1, step_speed)
                                    
                                    # Update current position
                                    current_robot_positions = safe_step_positions.copy()
                                    
                                    # Always step the simulation
                                    with pybullet_api_lock:
                                        pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                                    
                                    # Wait for step completion (shorter for simulation)
                                    time.sleep(0.08)  # 80ms between steps
                                    
                                except Exception as e:
                                    print(f"[Main] ❌ Error in interpolation step {i+1}: {e}")
                                    break
                            
                            # Analyze completed movement
                            analyzer.finish_movement(movement_id)
                            print(f"[Main] ✅ Smooth simulation movement completed!")
                            
                        else:
                            print("[Main] Movement too small, direct positioning...")
                            direct_start_time = time.time()
                            try:
                                robo.move_abs_with_speed(safe_target_positions, speed=rl_config.MAX_SPEED * 0.5)
                                direct_duration = time.time() - direct_start_time
                                print(f"    ⏱️  Direct movement took {direct_duration*1000:.0f}ms")
                                current_robot_positions = safe_target_positions.copy()
                            except Exception as e:
                                print(f"[Main] ❌ Error in direct movement: {e}")
                                continue
                        
                        # Show final end-effector position
                        if sim_data_manager.latest_relative_pos is not None:
                            pos = sim_data_manager.latest_relative_pos
                            print(f'[Main] Final EEF position: X={pos[0]:.4f}, Y={pos[1]:.4f}, Z={pos[2]:.4f}')
                            
                        # Show final joint angles
                        final_joint_angles = robo.get_Position()
                        if final_joint_angles:
                            angles_str = [f'{angle[0]:.2f}°' if angle[0] is not None else 'N/A' 
                                        for angle in final_joint_angles]
                            print(f"[Main] Final Joint Angles: {angles_str}")
                        
                        last_moveit_positions = moveit_positions.copy()
                        print("=" * 60)
                        
            # Always step the simulation to keep it running
            with pybullet_api_lock:
                pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                    
            time.sleep(0.1)  # 10Hz main loop
            
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