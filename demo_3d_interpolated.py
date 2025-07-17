#!/usr/bin/env python3
"""
🎪 DEMO: 3D Interpolated PyBullet Robot Simulation
==================================================

This script demonstrates the 3D interpolated version of the MoveIt to PyBullet synchronization system.
It shows ultra-smooth robot motion using 5th degree polynomial interpolation.

Features:
- 5th degree polynomial interpolation for ultra-smooth motion
- Buffered trajectory execution with predictive planning
- 50Hz interpolated output for fluid motion
- Robust error handling and safety checks
- Real-time visualization of interpolation quality

Usage:
    python3 demo_3d_interpolated.py

Requirements:
    - PyBullet: pip install pybullet
    - scipy: pip install scipy
    - numpy: pip install numpy
"""

import sys
import os
import time
import threading
import signal
import math
import numpy as np

# Add the real_robot directory to the path
sys.path.append('/home/luca/Documents/GitHub/adaptive_robot_planning/real_robot')

try:
    from main_sim_ros_bridge_3d_interpolated import InterpolatedROSBridgeDataReader, map_moveit_joints_to_pybullet
    from sim_robot import SimRobot
    from safety import SafetyWatchdogSim
    from sim_sensor import SimNatNetDataHandler
    import rl_config
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure you're running this script from the correct directory")
    print("and that all required files are present in the real_robot folder.")
    sys.exit(1)

def clamp_joint_limits(joint_positions):
    """Clamp joint positions to safe limits"""
    if not joint_positions:
        return joint_positions
        
    # UR5 joint limits (in degrees)
    joint_limits = [
        [-360, 360],  # shoulder_pan_joint
        [-360, 360],  # shoulder_lift_joint
        [-360, 360],  # elbow_joint
        [-360, 360],  # wrist_1_joint
        [-360, 360],  # wrist_2_joint
        [-360, 360]   # wrist_3_joint
    ]
    
    clamped = []
    for i, pos in enumerate(joint_positions):
        if i < len(joint_limits):
            min_val, max_val = joint_limits[i]
            clamped.append(max(min_val, min(max_val, pos)))
        else:
            clamped.append(pos)
    
    return clamped

class Demo3DInterpolated:
    def __init__(self):
        self.running = False
        self.robot = None
        self.safety_watchdog = None
        self.ros_bridge = None
        self.sensor_handler = None
        
        # Demo parameters
        self.demo_duration = 60  # seconds
        self.trajectory_frequency = 20  # Hz
        self.interpolation_quality_threshold = 0.95
        
        # Statistics
        self.stats = {
            'total_commands': 0,
            'interpolated_commands': 0,
            'dropped_commands': 0,
            'average_smoothness': 0.0,
            'max_velocity': 0.0,
            'max_acceleration': 0.0
        }
        
        # Previous position for velocity/acceleration calculation
        self.prev_position = None
        self.prev_velocity = None
        self.prev_time = None
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Received interrupt signal. Shutting down demo...")
        self.running = False
        
    def generate_demo_trajectory(self):
        """Generate a complex demo trajectory to showcase interpolation"""
        import json
        
        joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint', 
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ]
        
        print("🎭 Generating complex demo trajectory...")
        
        # Generate trajectory for demo_duration seconds
        total_points = int(self.demo_duration * self.trajectory_frequency)
        
        def trajectory_thread():
            for i in range(total_points):
                if not self.running:
                    break
                    
                t = i / self.trajectory_frequency
                
                # Complex multi-frequency motion pattern
                joint_positions = [
                    # Shoulder pan: slow figure-8 pattern
                    60 * math.sin(t * 0.2) * math.cos(t * 0.1),
                    
                    # Shoulder lift: oscillating around -45°
                    -45 + 40 * math.sin(t * 0.3) * math.cos(t * 0.05),
                    
                    # Elbow: complex wave around -90°
                    -90 + 50 * math.sin(t * 0.4) * math.sin(t * 0.15),
                    
                    # Wrist 1: multi-frequency oscillation
                    -85 + 30 * math.sin(t * 0.5) * math.cos(t * 0.25),
                    
                    # Wrist 2: rapid oscillation
                    20 * math.sin(t * 0.8) * math.cos(t * 0.3),
                    
                    # Wrist 3: slow complex pattern
                    90 * math.sin(t * 0.15) * math.sin(t * 0.08)
                ]
                
                # Create data structure
                data = {
                    'timestamp': time.time(),
                    'joint_names': joint_names,
                    'joint_positions': joint_positions
                }
                
                # Write to file
                with open('/tmp/moveit_to_pybullet_data.json', 'w') as f:
                    json.dump(data, f, indent=2)
                
                if i % 100 == 0:
                    print(f"📊 Generated {i}/{total_points} trajectory points ({100*i/total_points:.1f}%)")
                
                time.sleep(1.0 / self.trajectory_frequency)
                
        # Start trajectory generation in background
        trajectory_thread = threading.Thread(target=trajectory_thread)
        trajectory_thread.daemon = True
        trajectory_thread.start()
        
        return trajectory_thread
        
    def calculate_motion_quality(self, current_position, timestamp):
        """Calculate motion quality metrics"""
        if self.prev_position is None:
            self.prev_position = current_position
            self.prev_time = timestamp
            return
            
        dt = timestamp - self.prev_time
        if dt <= 0:
            return
            
        # Calculate velocity
        velocity = [(curr - prev) / dt for curr, prev in zip(current_position, self.prev_position)]
        velocity_magnitude = math.sqrt(sum(v**2 for v in velocity))
        
        # Calculate acceleration if we have previous velocity
        if self.prev_velocity is not None:
            acceleration = [(curr - prev) / dt for curr, prev in zip(velocity, self.prev_velocity)]
            acceleration_magnitude = math.sqrt(sum(a**2 for a in acceleration))
            
            # Update statistics
            self.stats['max_velocity'] = max(self.stats['max_velocity'], velocity_magnitude)
            self.stats['max_acceleration'] = max(self.stats['max_acceleration'], acceleration_magnitude)
            
            # Calculate smoothness (inverse of acceleration magnitude)
            smoothness = 1.0 / (1.0 + acceleration_magnitude)
            self.stats['average_smoothness'] = (self.stats['average_smoothness'] * 0.9 + smoothness * 0.1)
        
        # Update previous values
        self.prev_position = current_position
        self.prev_velocity = velocity
        self.prev_time = timestamp
        
    def print_statistics(self):
        """Print real-time statistics"""
        print("\n" + "="*80)
        print("🎪 3D INTERPOLATED SIMULATION - REAL-TIME STATISTICS")
        print("="*80)
        print(f"📊 Total Commands:      {self.stats['total_commands']}")
        print(f"🎯 Interpolated:        {self.stats['interpolated_commands']}")
        print(f"❌ Dropped:            {self.stats['dropped_commands']}")
        print(f"🎪 Smoothness:         {self.stats['average_smoothness']:.3f}")
        print(f"⚡ Max Velocity:       {self.stats['max_velocity']:.2f} rad/s")
        print(f"🚀 Max Acceleration:   {self.stats['max_acceleration']:.2f} rad/s²")
        
        # Buffer status
        if self.ros_bridge:
            buffer_status = self.ros_bridge.get_buffer_status()
            print(f"📦 Buffer Status:      {buffer_status['pending_points']}/{buffer_status['total_points']} points")
            print(f"🔄 Interpolation Ready: {'✅' if buffer_status['interpolation_ready'] else '❌'}")
            print(f"⏰ Buffer Time Span:   {buffer_status['time_span']:.1f}s")
        
        print("="*80)
        
    def run_demo(self):
        """Main demo loop"""
        print("🎪 Starting 3D Interpolated Robot Simulation Demo")
        print("="*60)
        
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Initialize robot
            print("🤖 Initializing PyBullet robot...")
            self.robot = SimRobot()
            if not self.robot.init_bus():
                print("❌ Failed to initialize PyBullet simulation")
                return
            self.robot.init_motors()
            
            # Initialize safety watchdog
            print("🛡️  Initializing safety watchdog...")
            self.safety_watchdog = SafetyWatchdogSim()
            self.safety_watchdog.start()
            
            # Initialize sensor handler (dummy for simulation)
            print("📡 Initializing sensor handler...")
            self.sensor_handler = SimNatNetDataHandler()
            
            # Initialize ROS bridge reader
            print("🌉 Initializing 3D interpolated ROS bridge...")
            self.ros_bridge = InterpolatedROSBridgeDataReader(
                buffer_size=100,
                max_age_seconds=5.0
            )
            self.ros_bridge.start_reading()
            
            # Start demo trajectory generation
            print("🎭 Starting demo trajectory generation...")
            trajectory_thread = self.generate_demo_trajectory()
            
            # Main simulation loop
            print("🎪 Starting 3D interpolated simulation loop...")
            print("   Press Ctrl+C to stop the demo")
            print("="*60)
            
            self.running = True
            loop_count = 0
            
            while self.running:
                loop_start = time.time()
                
                # Get interpolated trajectory
                interpolated_trajectory = self.ros_bridge.get_interpolated_trajectory(duration_seconds=0.1)
                
                if interpolated_trajectory:
                    # Execute interpolated points
                    for trajectory_point in interpolated_trajectory:
                        if not self.running:
                            break
                            
                        moveit_positions = trajectory_point['positions']
                        timestamp = trajectory_point['timestamp']
                        
                        # Map to PyBullet joint order
                        pybullet_positions = map_moveit_joints_to_pybullet(
                            moveit_positions,
                            ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
                             'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
                        )
                        
                        if pybullet_positions:
                            # Apply joint limits
                            safe_positions = clamp_joint_limits(pybullet_positions)
                            
                            # Move robot
                            self.robot.move_to_joint_positions(safe_positions)
                            
                            # Calculate motion quality
                            self.calculate_motion_quality(safe_positions, timestamp)
                            
                            # Update statistics
                            self.stats['total_commands'] += 1
                            self.stats['interpolated_commands'] += 1
                            
                            # Short sleep for interpolated motion
                            time.sleep(0.02)  # 50Hz
                        else:
                            self.stats['dropped_commands'] += 1
                else:
                    # No interpolated trajectory available
                    self.stats['dropped_commands'] += 1
                    time.sleep(0.05)  # Wait a bit more
                
                loop_count += 1
                
                # Print statistics every 5 seconds
                if loop_count % 250 == 0:  # Approximately every 5 seconds at 50Hz
                    self.print_statistics()
                    
                # Check if demo duration exceeded
                if loop_count > self.demo_duration * 50:  # 50Hz * duration
                    print("⏰ Demo duration completed!")
                    break
                    
        except Exception as e:
            print(f"❌ Error during demo: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            print("\n🧹 Cleaning up...")
            self.running = False
            
            if self.ros_bridge:
                self.ros_bridge.stop_reading()
                
            if self.safety_watchdog:
                self.safety_watchdog.stop()
                
            if self.robot:
                self.robot.shutdown()
                
            print("✅ Demo completed successfully!")
            self.print_statistics()


def main():
    """Main entry point"""
    print("🎪 3D INTERPOLATED ROBOT SIMULATION DEMO")
    print("=" * 50)
    print("This demo showcases ultra-smooth robot motion using")
    print("5th degree polynomial interpolation between trajectory points.")
    print("=" * 50)
    
    demo = Demo3DInterpolated()
    demo.run_demo()


if __name__ == "__main__":
    main()
