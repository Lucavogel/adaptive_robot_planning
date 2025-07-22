#!/usr/bin/env python3
"""
PyBullet simulation with COMPLETE MoveIt trajectory execution using global interpolation.
This version processes entire MoveIt trajectories with smooth global interpolation.
"""

import logging
import numpy as np
import time
import threading
import json
import os
from scipy.interpolate import CubicSpline

from sim_robot import SimRobot
from safety import SafetyWatchdogSim
from sim_sensor import SimNatNetDataHandler
import rl_config

class FullTrajectoryROSBridgeReader:
    """
    ROS Bridge reader for COMPLETE MoveIt trajectories with global interpolation.
    """
    
    def __init__(self, data_file_path='/tmp/moveit_full_trajectory.json'):
        self.data_file_path = data_file_path
        self.latest_trajectory_data = None
        self.latest_timestamp = 0
        self.data_lock = threading.Lock()
        self.running = False
        self.reader_thread = None
        
    def start_reading(self, update_interval=0.1):
        """Start reading trajectory data in background thread."""
        self.running = True
        self.reader_thread = threading.Thread(target=self._read_loop, args=(update_interval,))
        self.reader_thread.daemon = True
        self.reader_thread.start()
        print(f"[FullTrajectoryROS] Started reading from {self.data_file_path}")
        
    def _read_loop(self, update_interval):
        """Background thread to read trajectory data."""
        startup_delay = 3.0  # Wait 3 seconds before processing
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
                    
                    # Check if this is new data
                    if data.get('timestamp', 0) > self.latest_timestamp:
                        with self.data_lock:
                            self.latest_trajectory_data = data
                            self.latest_timestamp = data.get('timestamp', 0)
                        print(f"[FullTrajectoryROS] 🆕 New trajectory: {len(data.get('trajectory_waypoints', []))} waypoints")
                        
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                pass
            
            time.sleep(update_interval)
    
    def get_latest_trajectory(self):
        """Get the latest complete trajectory data."""
        with self.data_lock:
            if self.latest_trajectory_data:
                return self.latest_trajectory_data.copy()
        return None
    
    def stop_reading(self):
        """Stop the reading thread."""
        self.running = False
        if self.reader_thread:
            self.reader_thread.join()

class GlobalTrajectoryInterpolator:
    """
    Global interpolation for complete MoveIt trajectories.
    PRE-CALCULATES everything at once, then executes rapidly.
    """
    
    def __init__(self, interpolation_dt=0.05):  # 50ms = 20Hz plus rapide et suffisant
        self.interpolation_dt = interpolation_dt
        self.current_interpolated_trajectory = None
        self.current_step = 0
        self.interpolation_complete = False
        
    def interpolate_full_trajectory(self, waypoints):
        """
        SUPER FAST OPTIMIZATION: Pre-calculate avec interpolation linéaire rapide!
        Fini les calculs longs - on utilise une méthode plus simple et plus rapide.
        """
        print(f"[GlobalTrajectoryInterpolator] 🚀 CALCUL RAPIDE avec {len(waypoints)} waypoints")
        start_time = time.time()
        
        # Prepare waypoints data - FIXED: Use correct key names
        times = np.array([wp['time_from_start'] for wp in waypoints])
        positions = np.array([wp['positions'] for wp in waypoints])
        
        if len(times) < 2:
            print("[GlobalTrajectoryInterpolator] Need at least 2 waypoints")
            return []
            
        # Handle case where times are all zero (no timing info)
        if np.all(times == 0):
            total_duration = len(waypoints) * 0.8  # Plus rapide: 0.8s par waypoint
            times = np.linspace(0, total_duration, len(waypoints))
            print(f"[GlobalTrajectoryInterpolator] No timing info, using {total_duration:.1f}s total duration")
            
        total_duration = times[-1] - times[0]
        if total_duration <= 0:
            print("[GlobalTrajectoryInterpolator] Invalid time sequence")
            return []
            
        # Generate time grid - FEWER STEPS for faster calculation
        num_steps = int(total_duration / self.interpolation_dt) + 1
        interpolation_times = np.linspace(times[0], times[-1], num_steps)
        
        print(f"[GlobalTrajectoryInterpolator] Creating {num_steps} steps (dt={self.interpolation_dt}s)")
        
        # SUPER FAST: Use LINEAR interpolation instead of cubic splines
        num_joints = len(positions[0])
        interpolated_positions = np.zeros((num_steps, num_joints))
        
        # Vectorized LINEAR interpolation - MUCH FASTER than cubic splines
        for joint_idx in range(num_joints):
            joint_positions = positions[:, joint_idx]
            interpolated_positions[:, joint_idx] = np.interp(interpolation_times, times, joint_positions)
        
        # Build complete trajectory - PRE-CALCULATED
        interpolated_trajectory = []
        for i in range(num_steps):
            interpolated_trajectory.append({
                'time': interpolation_times[i],
                'positions': interpolated_positions[i].tolist(),
                'dt': self.interpolation_dt
            })
        
        calc_time = time.time() - start_time
        print(f"[GlobalTrajectoryInterpolator] ✅ CALCUL TERMINÉ en {calc_time:.2f}s!")
        print(f"[GlobalTrajectoryInterpolator] {len(interpolated_trajectory)} steps prêts pour exécution RAPIDE")
        
        # Store for rapid execution
        self.current_interpolated_trajectory = interpolated_trajectory
        self.current_step = 0
        self.interpolation_complete = False
        
        return interpolated_trajectory
    
    def get_next_interpolated_position(self):
        """
        Get next pre-calculated position instantly.
        NO calculation overhead - just array lookup for maximum speed!
        """
        if (self.current_interpolated_trajectory is None or 
            self.current_step >= len(self.current_interpolated_trajectory)):
            return None
        
        # FAST: Direct array access to pre-calculated positions
        position_data = self.current_interpolated_trajectory[self.current_step]
        self.current_step += 1
        
        # Check if trajectory is complete
        if self.current_step >= len(self.current_interpolated_trajectory):
            self.interpolation_complete = True
        
        # Return just the joint positions for rapid execution
        return position_data['positions']
    
    def get_progress(self):
        """Get current progress through trajectory (0.0 to 1.0)."""
        if self.current_interpolated_trajectory is None:
            return 0.0
        total_steps = len(self.current_interpolated_trajectory)
        return min(self.current_step / total_steps, 1.0) if total_steps > 0 else 0.0
    
    def is_complete(self):
        """Check if trajectory execution is complete."""
        return self.interpolation_complete
    
    def reset(self):
        """Reset interpolator for new trajectory."""
        self.current_interpolated_trajectory = None
        self.current_step = 0
        self.interpolation_complete = False

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
    # Clear old data file to prevent immediate movement from stale data
    data_file_path = '/tmp/moveit_full_trajectory.json'
    if os.path.exists(data_file_path):
        print(f"[Main] Clearing old MoveIt trajectory file: {data_file_path}")
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
    
    # Initialize full trajectory ROS bridge reader
    trajectory_reader = FullTrajectoryROSBridgeReader()
    trajectory_reader.start_reading(update_interval=0.1)
    
    # Initialize global interpolator
    interpolator = GlobalTrajectoryInterpolator(interpolation_dt=0.05)  # 50ms steps = 20Hz optimisé
    
    print("[Main] PyBullet robot initialized with FULL TRAJECTORY INTERPOLATION...")
    print("[Main] Features:")
    print("  - Global cubic spline interpolation across entire trajectory")
    print("  - Smooth execution of complete MoveIt paths")
    print("  - 50ms interpolation steps for precision")
    print("  - Safety-focused timing and limits")
    print("  - 3-second startup delay")
    print("[Main] Plan a complete trajectory in MoveIt and watch smooth global execution!")
    print("[Main] Robot will wait 3 seconds before processing MoveIt trajectories...")
    
    try:
        trajectory_count = 0
        current_trajectory_executing = False
        
        while True:
            if watchdog._exception_event.is_set():
                print("\n[Main] Watchdog thread reported a critical exception. Stopping.")
                robo.enter_emergency_recovery()
                break
            
            # Check for new complete trajectory
            trajectory_data = trajectory_reader.get_latest_trajectory()
            
            if trajectory_data and not current_trajectory_executing:
                trajectory_waypoints = trajectory_data.get('trajectory_waypoints', [])
                joint_names = trajectory_data.get('joint_names', [])
                
                if len(trajectory_waypoints) >= 2:
                    trajectory_count += 1
                    current_trajectory_executing = True
                    
                    print(f"\n[Main] ===== FULL TRAJECTORY EXECUTION #{trajectory_count} =====")
                    print(f"[Main] Received trajectory with {len(trajectory_waypoints)} waypoints")
                    print(f"[Main] Joint names: {joint_names}")
                    
                    # Map waypoints to simulation format
                    mapped_waypoints = []
                    for i, waypoint in enumerate(trajectory_waypoints):
                        moveit_positions = waypoint['positions']
                        sim_positions = map_moveit_joints_to_simulation(moveit_positions, joint_names)
                        
                        if sim_positions:
                            # Apply safety limits
                            safe_positions = []
                            for j, angle in enumerate(sim_positions):
                                if j < len(rl_config.JOINT_LIMITS):
                                    min_limit, max_limit = rl_config.JOINT_LIMITS[j]
                                    clamped_angle = np.clip(angle, min_limit, max_limit)
                                    safe_positions.append(float(clamped_angle))
                                    
                                    if abs(clamped_angle - angle) > 0.1:
                                        print(f"[Main] ⚠️ Waypoint {i}, Joint {j} clamped from {angle:.1f}° to {clamped_angle:.1f}°")
                                else:
                                    safe_positions.append(float(angle))
                            
                            mapped_waypoint = {
                                'positions': safe_positions,
                                'time_from_start': waypoint['time_from_start']
                            }
                            mapped_waypoints.append(mapped_waypoint)
                            
                            if i == 0:
                                print(f"[Main] Start position: {[f'{pos:.1f}°' for pos in safe_positions]}")
                            elif i == len(trajectory_waypoints) - 1:
                                print(f"[Main] End position: {[f'{pos:.1f}°' for pos in safe_positions]}")
                    
                    if len(mapped_waypoints) >= 2:
                        # Generate global interpolation - WAIT until calculation is complete
                        print(f"[Main] Generating global interpolation for {len(mapped_waypoints)} waypoints...")
                        print(f"[Main] ⏳ ATTENTE: Calculs en cours, robot en pause...")
                        
                        interpolated_trajectory = interpolator.interpolate_full_trajectory(mapped_waypoints)
                        
                        # CRITICAL: Only start execution when calculation is 100% complete
                        if len(interpolated_trajectory) > 0:
                            print(f"[Main] ✅ CALCULS TERMINÉS! Début de l'exécution avec {len(interpolated_trajectory)} steps...")
                            trajectory_start_time = time.time()
                            
                            # Execute interpolated trajectory - OPTIMIZED execution
                            step_count = 0
                            while not interpolator.is_complete():
                                next_position = interpolator.get_next_interpolated_position()
                                if next_position is None:
                                    break
                                
                                step_count += 1
                                progress = interpolator.get_progress()
                                
                                # Show progress every 20 steps (every 1 second at 20Hz)
                                if step_count % 20 == 0 or step_count == 1:
                                    print(f"[Main] Step {step_count}/{len(interpolated_trajectory)} ({progress*100:.1f}%): {[f'{pos:.1f}°' for pos in next_position]}")
                                
                                try:
                                    # Send position to robot with MODERATE speed for stability
                                    robo.move_abs_with_speed(next_position, speed=400)
                                    
                                    # Always step the simulation
                                    with pybullet_api_lock:
                                        pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                                    
                                    # OPTIMIZED timing: 50ms timestep (20Hz) for good balance
                                    time.sleep(interpolator.interpolation_dt)
                                    
                                except Exception as e:
                                    print(f"[Main] ❌ Error in trajectory step {step_count}: {e}")
                                    break
                            
                            # Trajectory execution complete
                            total_execution_time = time.time() - trajectory_start_time
                            print(f"\n[Main] ✅ FULL TRAJECTORY EXECUTION COMPLETE!")
                            print(f"[Main] Executed {step_count} interpolated steps")
                            print(f"[Main] Total execution time: {total_execution_time:.2f}s")
                            print(f"[Main] Average step time: {total_execution_time/step_count*1000:.1f}ms")
                            
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
                            
                            # Reset interpolator for next trajectory
                            interpolator.reset()
                            
                        else:
                            print("[Main] ❌ Failed to generate interpolated trajectory")
                    else:
                        print("[Main] ❌ Not enough valid waypoints after mapping")
                    
                    current_trajectory_executing = False
                    print("=" * 80)
            
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
        trajectory_reader.stop_reading()
        watchdog.stop()
        robo.shutdown()
        print("[Main] Shutdown complete.")
