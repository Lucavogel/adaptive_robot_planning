#!/usr/bin/env python3
"""
MoveIt Trajectory Bridge for COMPLETE trajectory capture.
Captures entire MoveIt trajectories and saves them for global interpolation.
"""

import rclpy
from rclpy.node import Node
import json
import time
import os
import numpy as np

from moveit_msgs.msg import DisplayTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint

class MoveItFullTrajectoryBridge(Node):
    
    def __init__(self):
        super().__init__('moveit_full_trajectory_bridge')
        
        # Subscribe to MoveIt trajectory display topic
        self.trajectory_subscriber = self.create_subscription(
            DisplayTrajectory,
            '/move_group/display_planned_path',
            self.trajectory_callback,
            10
        )
        
        # Also try alternative topic names
        self.trajectory_subscriber2 = self.create_subscription(
            DisplayTrajectory,
            '/display_planned_path',
            self.trajectory_callback,
            10
        )
        
        # Data file for communication with robot controller
        self.data_file = '/tmp/moveit_full_trajectory.json'
        
        # Expected joint names for Lynx robot
        self.expected_joints = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_5', 'joint_6']
        
        # Bridge ready flag
        self.bridge_ready = False
        self.startup_time = time.time()
        
        # Setup startup delay
        self.get_logger().info("MoveIt Full Trajectory Bridge starting...")
        self.get_logger().info(f"Will save complete trajectories to: {self.data_file}")
        self.get_logger().info("Waiting 3 seconds before processing trajectories...")
        
        # Timer to mark bridge as ready after startup delay (one-time)
        self.create_timer(3.0, self.mark_ready)
        self._ready_timer_called = False
        
    def mark_ready(self):
        """Mark the bridge as ready after startup delay."""
        if not self._ready_timer_called:
            self.bridge_ready = True
            self.get_logger().info("✅ MoveIt Full Trajectory Bridge READY!")
            self.get_logger().info("Plan trajectories in MoveIt to see complete trajectory execution!")
            self._ready_timer_called = True
        
    def trajectory_callback(self, msg):
        """Process complete MoveIt trajectory."""
        if not self.bridge_ready:
            self.get_logger().info("Bridge not ready yet, ignoring trajectory...")
            return
            
        try:
            # Extract trajectory from message
            if len(msg.trajectory) == 0:
                self.get_logger().warn("Received empty trajectory")
                return
                
            # Get the robot trajectory (first trajectory in the message)
            robot_trajectory = msg.trajectory[0].joint_trajectory
            joint_names = robot_trajectory.joint_names
            trajectory_points = robot_trajectory.points
            
            if len(trajectory_points) == 0:
                self.get_logger().warn("Trajectory has no points")
                return
                
            self.get_logger().info(f"📋 Received COMPLETE trajectory:")
            self.get_logger().info(f"   Joints: {joint_names}")
            self.get_logger().info(f"   Waypoints: {len(trajectory_points)}")
            
            # Validate joint names (ensure they match expected Lynx joints)
            if not self.validate_joint_names(joint_names):
                self.get_logger().error("Joint names don't match expected Lynx joints!")
                return
                
            # Convert trajectory points to our format
            trajectory_waypoints = []
            for i, point in enumerate(trajectory_points):
                # Convert radians to degrees for consistency with simulation
                positions_deg = [float(np.degrees(pos)) for pos in point.positions]
                
                # Extract time from start (convert from Duration to float seconds)
                time_from_start = float(point.time_from_start.sec) + float(point.time_from_start.nanosec) / 1e9
                
                waypoint = {
                    'positions': positions_deg,
                    'time_from_start': time_from_start
                }
                trajectory_waypoints.append(waypoint)
                
                # Log first and last waypoints
                if i == 0:
                    self.get_logger().info(f"   Start: {[f'{pos:.1f}°' for pos in positions_deg]} at t={time_from_start:.2f}s")
                elif i == len(trajectory_points) - 1:
                    self.get_logger().info(f"   End:   {[f'{pos:.1f}°' for pos in positions_deg]} at t={time_from_start:.2f}s")
            
            # Create complete trajectory data
            trajectory_data = {
                'timestamp': time.time(),
                'joint_names': joint_names,
                'trajectory_waypoints': trajectory_waypoints,
                'total_waypoints': len(trajectory_waypoints),
                'total_duration': trajectory_waypoints[-1]['time_from_start'] if trajectory_waypoints else 0.0
            }
            
            # Save to file for simulation/robot controller
            self.save_trajectory_data(trajectory_data)
            
            self.get_logger().info(f"✅ Saved complete trajectory with {len(trajectory_waypoints)} waypoints")
            self.get_logger().info(f"   Total duration: {trajectory_data['total_duration']:.2f}s")
            
        except Exception as e:
            self.get_logger().error(f"Error processing trajectory: {str(e)}")
            
    def validate_joint_names(self, joint_names):
        """Validate that joint names match expected Lynx robot joints."""
        if len(joint_names) != len(self.expected_joints):
            self.get_logger().error(f"Expected {len(self.expected_joints)} joints, got {len(joint_names)}")
            return False
            
        for expected, received in zip(self.expected_joints, joint_names):
            if expected != received:
                self.get_logger().error(f"Joint name mismatch: expected {expected}, got {received}")
                return False
                
        return True
        
    def save_trajectory_data(self, trajectory_data):
        """Save trajectory data to JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            # Write atomically (write to temp file, then rename)
            temp_file = self.data_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(trajectory_data, f, indent=2)
                
            # Atomic rename
            os.rename(temp_file, self.data_file)
            
        except Exception as e:
            self.get_logger().error(f"Failed to save trajectory data: {str(e)}")

def main(args=None):
    rclpy.init(args=args)
    
    print("=" * 60)
    print("🚀 MoveIt FULL TRAJECTORY Bridge")
    print("=" * 60)
    print("This bridge captures COMPLETE MoveIt trajectories")
    print("for smooth global interpolation execution.")
    print("")
    print("Features:")
    print("  - Captures entire planned trajectories")
    print("  - Preserves timing information")
    print("  - Converts to simulation-friendly format")
    print("  - Enables global interpolation")
    print("")
    print("Usage:")
    print("  1. Start this bridge")
    print("  2. Start the simulation controller")
    print("  3. Plan trajectories in MoveIt")
    print("  4. Watch smooth complete execution!")
    print("=" * 60)
    
    node = MoveItFullTrajectoryBridge()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down MoveIt Full Trajectory Bridge...")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
