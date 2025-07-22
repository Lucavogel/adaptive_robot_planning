#!/usr/bin/env python3
"""
ROS2 Bridge to capture complete MoveIt trajectory and send to real robot.
This captures the full planned path, not just the goal position.
"""

import rclpy
from rclpy.node import Node
from moveit_msgs.msg import DisplayTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
import json
import time
import math

class MoveItTrajectoryBridge(Node):
    """Bridge to capture complete MoveIt trajectories for smooth robot execution."""
    
    def __init__(self):
        super().__init__('moveit_trajectory_bridge')
        
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
        self.create_timer(3.0, self.enable_processing)  # 3 second delay
        
        # Setup topic discovery timer
        self.create_timer(5.0, self.list_available_topics)  # List topics every 5s
        
        self.get_logger().info("🚀 MoveIt TRAJECTORY Bridge started")
        self.get_logger().info("Listening for FULL trajectories on:")
        self.get_logger().info("  - /move_group/display_planned_path")
        self.get_logger().info("  - /display_planned_path")
        self.get_logger().info("Startup delay: 3.0s - ignoring initial data")
        
    def enable_processing(self):
        """Enable trajectory processing after startup delay."""
        self.bridge_ready = True
        self.get_logger().info("🟢 Bridge ready to process MoveIt FULL trajectories")
        
    def trajectory_callback(self, msg):
        """Process incoming trajectory messages."""
        if not self.bridge_ready:
            return
            
        try:
            # Extract trajectory from the message
            if not msg.trajectory or len(msg.trajectory) == 0:
                self.get_logger().warn("Empty trajectory received")
                return
                
            # Get the robot trajectory (first trajectory in the message)
            robot_trajectory = msg.trajectory[0].joint_trajectory
            
            if not robot_trajectory.points or len(robot_trajectory.points) == 0:
                self.get_logger().warn("No trajectory points found")
                return
                
            # Extract joint names
            joint_names = robot_trajectory.joint_names
            
            # Verify we have the expected joints
            if not all(joint in joint_names for joint in self.expected_joints):
                missing = [j for j in self.expected_joints if j not in joint_names]
                self.get_logger().warn(f"Missing expected joints: {missing}")
                return
                
            # Convert trajectory points to our format
            trajectory_waypoints = []
            for i, point in enumerate(robot_trajectory.points):
                # Map joint positions to our expected order
                mapped_positions = []
                for expected_joint in self.expected_joints:
                    if expected_joint in joint_names:
                        joint_idx = joint_names.index(expected_joint)
                        # Convert from radians to degrees
                        angle_deg = math.degrees(point.positions[joint_idx])
                        mapped_positions.append(angle_deg)
                    else:
                        mapped_positions.append(0.0)
                
                # Extract timing information if available
                time_from_start = 0.0
                if hasattr(point, 'time_from_start') and point.time_from_start:
                    time_from_start = point.time_from_start.sec + point.time_from_start.nanosec * 1e-9
                
                waypoint = {
                    'positions': mapped_positions,
                    'time_from_start': time_from_start,
                    'waypoint_index': i
                }
                trajectory_waypoints.append(waypoint)
            
            # Create complete trajectory data
            trajectory_data = {
                'trajectory_waypoints': trajectory_waypoints,
                'joint_names': self.expected_joints,
                'total_waypoints': len(trajectory_waypoints),
                'trajectory_duration': trajectory_waypoints[-1]['time_from_start'] if trajectory_waypoints else 0.0,
                'timestamp': time.time(),
                'robot_model': 'lynx_ses900',
                'bridge_ready': True,
                'trajectory_type': 'full_path'
            }
            
            # Write to file
            with open(self.data_file, 'w') as f:
                json.dump(trajectory_data, f, indent=2)
            
            self.get_logger().info(f"📍 Full trajectory saved: {len(trajectory_waypoints)} waypoints, "
                                 f"duration: {trajectory_data['trajectory_duration']:.2f}s")
            
            # Log first and last positions for debugging
            if len(trajectory_waypoints) >= 2:
                start_pos = [f"{pos:.1f}°" for pos in trajectory_waypoints[0]['positions']]
                end_pos = [f"{pos:.1f}°" for pos in trajectory_waypoints[-1]['positions']]
                self.get_logger().info(f"Start: {start_pos}")
                self.get_logger().info(f"End:   {end_pos}")
                
        except Exception as e:
            self.get_logger().error(f"Error processing trajectory: {e}")
            
    def list_available_topics(self):
        """List available topics to help debug."""
        try:
            topic_names_and_types = self.get_topic_names_and_types()
            trajectory_topics = []
            moveit_topics = []
            
            for topic_name, topic_types in topic_names_and_types:
                if 'trajectory' in topic_name.lower() or 'display' in topic_name.lower():
                    trajectory_topics.append(f"{topic_name} ({', '.join(topic_types)})")
                if 'move' in topic_name.lower():
                    moveit_topics.append(f"{topic_name} ({', '.join(topic_types)})")
            
            if trajectory_topics or moveit_topics:
                self.get_logger().info("🔍 Available topics for debugging:")
                for topic in trajectory_topics[:5]:  # Show first 5 trajectory topics
                    self.get_logger().info(f"  📍 {topic}")
                for topic in moveit_topics[:3]:  # Show first 3 moveit topics
                    self.get_logger().info(f"  🤖 {topic}")
            else:
                self.get_logger().info("🔍 No trajectory or MoveIt topics found yet...")
                
        except Exception as e:
            self.get_logger().warn(f"Could not list topics: {e}")

def main(args=None):
    rclpy.init(args=args)
    
    # Clean up old data file
    import os
    data_file = '/tmp/moveit_full_trajectory.json'
    if os.path.exists(data_file):
        os.remove(data_file)
        print(f"🧹 Cleaned up old trajectory data: {data_file}")
    
    node = MoveItTrajectoryBridge()
    
    try:
        print("🚀 MoveIt FULL Trajectory Bridge running...")
        print("   📂 Output file: /tmp/moveit_full_trajectory.json")
        print("   🎯 Captures complete planned paths from MoveIt")
        print("   ⏰ 3s startup delay to ignore old data")
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\n🛑 Bridge stopped by user")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
