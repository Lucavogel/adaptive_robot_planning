#!/usr/bin/env python3
"""
Real robot controller with smooth interpolation and motion planning.
This script reads joint positions from the ROS bridge and applies smooth interpolated movements to the real robot.
"""

import logging
import numpy as np
import time
import threading
import json
import os

from robot import Robot
from safety import SafetyWatchdog
import rl_config

class InterpolatedROSBridgeReader:
    """
    ROS Bridge reader with interpolation capabilities for smooth movement on real robot.
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
        
        while self.running:
            try:
                if os.path.exists(self.data_file_path):
                    with open(self.data_file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Only process data if bridge is ready and providing real data
                    if not data.get('bridge_ready', False):
                        if consecutive_errors == 0:  # Only log first time
                            print(f"[InterpolatedROSBridge] Bridge not ready yet, waiting...")
                        consecutive_errors += 1
                        time.sleep(update_interval)
                        continue
                        
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

class RealRobotInterpolator:
    """
    Handles smooth interpolation for real robot with safety considerations.
    """
    
    def __init__(self, interpolation_steps=6, position_tolerance=1.0, max_step_speed=300):
        self.interpolation_steps = interpolation_steps
        self.position_tolerance = position_tolerance  # degrees
        self.max_step_speed = max_step_speed  # LSS speed units
        
    def interpolate_to_target(self, current_positions, target_positions, steps=None):
        """
        Generate interpolated positions from current to target for real robot.
        
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
        
        # Adapt steps based on movement size for real robot (more conservative)
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
            # Use smooth easing function (ease-in-out for real robot)
            alpha = 3 * alpha ** 2 - 2 * alpha ** 3
            
            interp_pos = []
            for i in range(len(target_positions)):
                interp_val = current_positions[i] + alpha * (target_positions[i] - current_positions[i])
                interp_pos.append(interp_val)
                
            interpolated_positions.append(interp_pos)
            
        print(f"[RealRobotInterpolator] Generated {len(interpolated_positions)} steps for max movement {max_movement:.1f}°")
        return interpolated_positions
    
    def needs_interpolation(self, current_positions, target_positions):
        """Check if interpolation is needed based on position difference."""
        if current_positions is None or target_positions is None:
            return True
            
        max_diff = max(abs(target_positions[i] - current_positions[i]) 
                      for i in range(len(target_positions)))
        return max_diff > self.position_tolerance
    
    def calculate_step_speed(self, current_positions, target_positions, step_positions):
        """Calculate appropriate speed for this interpolation step."""
        # Calculate step distance
        step_distances = [abs(step_positions[i] - current_positions[i]) 
                         for i in range(len(step_positions))]
        max_step_distance = max(step_distances)
        
        # Adapt speed based on step size (use working speeds: 500-1300)
        if max_step_distance < 2.0:
            return min(self.max_step_speed * 0.4, 500)   # Minimum working speed: 500
        elif max_step_distance < 5.0:
            return min(self.max_step_speed * 0.6, 800)   # Medium speed: 800
        elif max_step_distance < 15.0:
            return min(self.max_step_speed * 0.8, 1000)  # High speed: 1000
        else:
            return self.max_step_speed  # Full speed: 1300 for large steps

class RealRobotMovementAnalyzer:
    """
    Analyzes real robot movement performance and provides metrics.
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
            
            print(f"    📊 REAL ROBOT MOVEMENT ANALYSIS:")
            print(f"       Total duration: {total_duration*1000:.0f}ms")
            print(f"       Average step time: {avg_step_time:.0f}ms")
            print(f"       Max joint movement: {movement['max_distance']:.2f}°")
            print(f"       Average speed: {avg_speed:.1f}°/s")
            print(f"       Steps used: {movement['num_steps']}")
            
            # Safety assessment for real robot
            if avg_step_time > 500:
                print(f"       ⚠️  Movement is very slow (safety-focused)")
            elif avg_step_time < 100:
                print(f"       ⚡ Movement is fast (check if safe)")
            else:
                print(f"       ✅ Movement timing is safe")

def map_moveit_joints_to_real_robot(moveit_positions, moveit_joint_names, real_robot_joint_count=6):
    """
    Maps MoveIt joint positions to real robot joint order (Lynx SES900) with offset compensation.
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
    
    # Offset compensation for real robot home position
    joint_offsets = [0, 0, 0, 0, 0, 0]  # Adjust as needed
    
    # Create mapping from MoveIt joint names to positions
    joint_dict = dict(zip(moveit_joint_names, moveit_positions))
    
    # Map to real robot order with offset compensation
    real_robot_positions = []
    for i, joint_name in enumerate(lynx_joint_names):
        if joint_name in joint_dict:
            compensated_position = joint_dict[joint_name] + joint_offsets[i]
            real_robot_positions.append(compensated_position)
        else:
            print(f"[Mapping] Warning: Joint {joint_name} not found in MoveIt data")
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
        natnet_data_handler=None,
        joint_limits=rl_config.JOINT_LIMITS,
        marker_radii=rl_config.MARKER_RADII,
    )
    robo.joint_watchdog = watchdog
    watchdog.start(check_interval=rl_config.WATCHDOG_INTERVAL)
    
    # Initialize interpolated ROS bridge reader
    ros_bridge = InterpolatedROSBridgeReader()
    ros_bridge.start_reading(update_interval=0.05)
    
    # Initialize interpolator for real robot
    interpolator = RealRobotInterpolator(
        interpolation_steps=6,     # Base number of steps (conservative for real robot)
        position_tolerance=1.0,    # Larger tolerance for real robot
        max_step_speed=rl_config.MAX_SPEED  # Use max speed from config (1300)
    )
    
    # Initialize movement analyzer
    analyzer = RealRobotMovementAnalyzer()
    
    print("[Main] Real robot initialized with SMOOTH INTERPOLATION...")
    print("[Main] Features:")
    print("  - Conservative interpolation (2-10 steps based on movement)")
    print("  - Adaptive speed control per step (500-1300)")
    print("  - Safety-focused timing")
    print("  - Position tolerance: 1.0°")
    print("[Main] Start your MoveIt planning and watch smooth real robot movement!")
    
    # Startup safety notice
    print("\n" + "="*60)
    print("🔄 SMART STARTUP: Waiting for NEW MoveIt commands...")
    print("   ✅ Old data is ignored - only fresh commands will be followed")
    print("   ✅ Robot will remain stationary until MoveIt sends new targets")
    print("   ⚠️  Make sure MoveIt is running before planning movements")
    print("="*60)
    
    try:
        command_count = 0
        last_moveit_positions = None
        current_robot_positions = None  # Track current position for interpolation
        moveit_command_received = False  # Track if we've received any new MoveIt commands
        startup_timestamp = time.time()  # Track startup time to ignore old data
        
        while True:
            if watchdog._exception_event.is_set():
                print("\n[Main] Watchdog thread reported a critical exception. Stopping.")
                robo.enter_emergency_recovery()
                break
                
            # Get latest joint positions from ROS bridge
            moveit_positions = ros_bridge.get_latest_joint_positions()
            moveit_joint_names = ros_bridge.get_joint_names()
            
            if moveit_positions and moveit_joint_names:
                # Get the timestamp of the current data
                moveit_timestamp = ros_bridge.latest_timestamp
                
                # Only process commands that are newer than our startup time (ignore old data)
                if moveit_timestamp > startup_timestamp:
                    # Check if positions have changed significantly
                    if last_moveit_positions is None or moveit_positions != last_moveit_positions:
                        
                        # If this is the first new command, announce it
                        if not moveit_command_received:
                            moveit_command_received = True
                            print(f"\n[Main] 🎯 First MoveIt command received! Starting to follow movements...")
                        
                        # Map MoveIt joints to real robot order
                        target_positions = map_moveit_joints_to_real_robot(
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
                                    print(f"[Main] Initial robot position: {[f'{pos:.1f}°' for pos in current_robot_positions]}")
                            
                            print(f"\n[Main] ===== SMOOTH REAL ROBOT MOVEMENT #{command_count} =====")
                            print(f"[Main] MoveIt target: {[f'{pos:.2f}°' for pos in moveit_positions]}")
                            print(f"[Main] Real robot target: {[f'{pos:.2f}°' for pos in target_positions]}")
                            
                            # DEBUG: Show current robot position for comparison
                            current_joint_angles = robo.get_Position()
                            if current_joint_angles:
                                current_angles_deg = [angle[0] if angle[0] is not None else 0.0 for angle in current_joint_angles]
                                print(f"[Main] 🤖 Current robot position: {[f'{pos:.2f}°' for pos in current_angles_deg]}")
                                
                                # Calculate and show the required movement
                                movement_required = [abs(target_positions[i] - current_angles_deg[i]) for i in range(len(target_positions))]
                                max_movement = max(movement_required)
                                print(f"[Main] 📏 Movement required: {[f'{mov:.1f}°' for mov in movement_required]} (max: {max_movement:.1f}°)")
                            
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
                                    
                                    # Send command to real robot
                                    try:
                                        print(f"[DEBUG] Sending command: {[f'{pos:.1f}°' for pos in safe_step_positions]} at speed {step_speed}")
                                        result = robo.move_abs_with_speed(safe_step_positions, speed=step_speed)
                                        print(f"[DEBUG] Command result: {result}")
                                        
                                        # Check if robot actually moved
                                        time.sleep(0.05)  # Brief pause for movement to start
                                        check_position = robo.get_Position()
                                        if check_position:
                                            check_angles = [angle[0] if angle[0] is not None else 0.0 for angle in check_position]
                                            print(f"[DEBUG] Robot position after command: {[f'{pos:.2f}°' for pos in check_angles]}")
                                        
                                        # Record step completion
                                        analyzer.record_step(movement_id, i+1, step_speed)
                                        
                                        # Update current position
                                        current_robot_positions = safe_step_positions.copy()
                                        
                                        # Wait for step completion (longer for real robot)
                                        time.sleep(0.15)  # 150ms between steps for safety
                                        
                                    except Exception as e:
                                        print(f"[Main] ❌ Error in interpolation step {i+1}: {e}")
                                        break
                                
                                # Analyze completed movement
                                analyzer.finish_movement(movement_id)
                                print(f"[Main] ✅ Smooth real robot movement completed!")
                                
                            else:
                                print("[Main] Movement too small, direct positioning...")
                                print(f"[DEBUG] Direct move to: {[f'{pos:.1f}°' for pos in safe_target_positions]}")
                                direct_start_time = time.time()
                                try:
                                    result = robo.move_abs_with_speed(safe_target_positions, speed=rl_config.MAX_SPEED * 0.5)
                                    print(f"[DEBUG] Direct move result: {result}")
                                    direct_duration = time.time() - direct_start_time
                                    print(f"    ⏱️  Direct movement took {direct_duration*1000:.0f}ms")
                                    current_robot_positions = safe_target_positions.copy()
                                except Exception as e:
                                    print(f"[Main] ❌ Error in direct movement: {e}")
                                    continue
                            
                            # Show final joint angles
                            final_joint_angles = robo.get_Position()
                            if final_joint_angles:
                                angles_str = [f'{angle[0]:.2f}°' if angle[0] is not None else 'N/A' 
                                            for angle in final_joint_angles]
                                print(f"[Main] Final Joint Angles: {angles_str}")
                            
                            last_moveit_positions = moveit_positions.copy()
                            print("=" * 60)
                        
            time.sleep(0.1)  # 10Hz main loop for real robot
            
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
