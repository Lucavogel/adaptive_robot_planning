#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped
import json
import threading
import time
import numpy as np

class MoveItToPyBulletBridge(Node):
    """
    ROS2 node that listens to MoveIt robot joint states and position commands,
    then forwards them to the PyBullet simulation via a shared data file or queue.
    """
    
    def __init__(self):
        super().__init__('moveit_to_pybullet_bridge')
        
        # Expected joint names for Lynx SES900 robot
        self.expected_lynx_joint_names = [
            'joint_1',  # Base rotation
            'joint_2',  # Shoulder
            'joint_3',  # Upper arm
            'joint_4',  # Forearm
            'joint_5',  # Wrist
            'joint_6'   # End-effector rotation
        ]
        
        # Subscriber for joint states from MoveIt
        self.joint_state_subscriber = self.create_subscription(
            JointState,
            '/joint_states',  # Topic where MoveIt publishes joint states
            self.joint_state_callback,
            10
        )
        
        # Subscriber for target poses from MoveIt
        self.pose_subscriber = self.create_subscription(
            PoseStamped,
            '/move_group/target_pose',  # Topic for target poses
            self.pose_callback,
            10
        )
        
        # Data storage for latest joint positions
        self.latest_joint_positions = None
        self.latest_target_pose = None
        self.joint_names = []
        
        # File path for sharing data with PyBullet simulation
        self.data_file_path = '/tmp/moveit_to_pybullet_data.json'
        
        # Initialize the data file
        self._init_data_file()
        
        self.get_logger().info('MoveIt to PyBullet Bridge started for Lynx SES900 robot')
        self.get_logger().info(f'Expected joint names: {self.expected_lynx_joint_names}')
        
    def _init_data_file(self):
        """Initialize the shared data file"""
        initial_data = {
            'joint_positions': None,
            'joint_names': [],
            'target_pose': None,
            'timestamp': time.time()
        }
        
        try:
            with open(self.data_file_path, 'w') as f:
                json.dump(initial_data, f)
        except Exception as e:
            self.get_logger().error(f'Failed to initialize data file: {e}')
    
    def joint_state_callback(self, msg):
        """Callback for joint state messages from MoveIt"""
        try:
            # Store joint names and positions
            new_joint_names = list(msg.name)
            new_joint_positions = list(msg.position)
            
            # Filter and order joints for Lynx SES900 robot
            filtered_joint_names, filtered_joint_positions = self._filter_lynx_joints(new_joint_names, new_joint_positions)
            
            # Check if this is a significant change (threshold 0.1 degrees)
            threshold_rad = np.radians(0.1)
            significant_change = False
            
            if self.latest_joint_positions is None:
                significant_change = True
            else:
                if len(filtered_joint_positions) == len(self.latest_joint_positions):
                    for i, (new_pos, old_pos) in enumerate(zip(filtered_joint_positions, self.latest_joint_positions)):
                        if abs(new_pos - old_pos) > threshold_rad:
                            significant_change = True
                            break
                else:
                    significant_change = True
            
            if significant_change:
                self.joint_names = filtered_joint_names
                self.latest_joint_positions = filtered_joint_positions
                
                # Convert radians to degrees for PyBullet
                joint_positions_deg = [np.degrees(pos) for pos in self.latest_joint_positions]
                
                # Update shared data file
                self._update_data_file(joint_positions_deg, self.joint_names)
                
                # Log the received joint positions (less verbose)
                joint_info = [f"{name}: {np.degrees(pos):.1f}°" for name, pos in zip(self.joint_names, self.latest_joint_positions)]
                self.get_logger().info(f'Lynx joints updated: {joint_info}')
            
        except Exception as e:
            self.get_logger().error(f'Error in joint state callback: {e}')
    
    def pose_callback(self, msg):
        """Callback for target pose messages from MoveIt"""
        try:
            self.latest_target_pose = {
                'position': [msg.pose.position.x, msg.pose.position.y, msg.pose.position.z],
                'orientation': [msg.pose.orientation.x, msg.pose.orientation.y, 
                              msg.pose.orientation.z, msg.pose.orientation.w]
            }
            
            self.get_logger().info(f'Received target pose: pos={self.latest_target_pose["position"]}, '
                                 f'orient={self.latest_target_pose["orientation"]}')
            
        except Exception as e:
            self.get_logger().error(f'Error in pose callback: {e}')
    
    def _update_data_file(self, joint_positions_deg, joint_names):
        """Update the shared data file with latest joint positions"""
        try:
            data = {
                'joint_positions': joint_positions_deg,
                'joint_names': joint_names,
                'target_pose': self.latest_target_pose,
                'timestamp': time.time(),
                'robot_model': 'lynx_ses900',
                'total_joints': len(joint_positions_deg)
            }
            
            with open(self.data_file_path, 'w') as f:
                json.dump(data, f)
                
        except Exception as e:
            self.get_logger().error(f'Failed to update data file: {e}')
    
    def _filter_lynx_joints(self, joint_names, joint_positions):
        """
        Filter and order joints for Lynx SES900 robot.
        Returns only the expected joints in the correct order.
        """
        try:
            filtered_names = []
            filtered_positions = []
            
            # Map received joints to expected Lynx joints
            for expected_joint in self.expected_lynx_joint_names:
                if expected_joint in joint_names:
                    idx = joint_names.index(expected_joint)
                    filtered_names.append(expected_joint)
                    filtered_positions.append(joint_positions[idx])
                else:
                    # Joint not found, log warning but continue
                    self.get_logger().warn(f'Expected joint {expected_joint} not found in received joints')
            
            if len(filtered_names) == 6:
                return filtered_names, filtered_positions
            else:
                self.get_logger().warn(f'Only {len(filtered_names)}/6 Lynx joints found in message')
                return filtered_names, filtered_positions
                
        except Exception as e:
            self.get_logger().error(f'Error filtering Lynx joints: {e}')
            return [], []


def main(args=None):
    rclpy.init(args=args)
    
    bridge_node = MoveItToPyBulletBridge()
    
    try:
        rclpy.spin(bridge_node)
    except KeyboardInterrupt:
        pass
    finally:
        bridge_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
