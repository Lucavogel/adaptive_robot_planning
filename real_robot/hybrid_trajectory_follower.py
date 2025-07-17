#!/usr/bin/env python3
"""
Hybrid approach for real robot - combines real-time and trajectory following
"""

import json
import time
import threading
from collections import deque
import numpy as np

class HybridTrajectoryFollower:
    """
    Hybrid approach: Buffer recent trajectory points but stay responsive
    """
    
    def __init__(self, buffer_size=50, max_age_seconds=2.0):
        self.buffer_size = buffer_size
        self.max_age_seconds = max_age_seconds
        self.trajectory_buffer = deque(maxlen=buffer_size)
        self.lock = threading.Lock()
        self.last_executed_time = 0
        
    def add_trajectory_point(self, positions, joint_names, timestamp):
        """Add a new trajectory point to the buffer"""
        with self.lock:
            point = {
                'positions': positions,
                'joint_names': joint_names,
                'timestamp': timestamp,
                'executed': False
            }
            self.trajectory_buffer.append(point)
            
    def get_next_command(self):
        """Get the next command to execute"""
        with self.lock:
            current_time = time.time()
            
            # Clean old points
            while (self.trajectory_buffer and 
                   current_time - self.trajectory_buffer[0]['timestamp'] > self.max_age_seconds):
                self.trajectory_buffer.popleft()
            
            # Find next unexecuted point
            for point in self.trajectory_buffer:
                if not point['executed']:
                    point['executed'] = True
                    return point['positions'], point['joint_names']
                    
            return None, None
    
    def has_pending_commands(self):
        """Check if there are pending commands"""
        with self.lock:
            return any(not point['executed'] for point in self.trajectory_buffer)
    
    def get_buffer_status(self):
        """Get buffer status for debugging"""
        with self.lock:
            total = len(self.trajectory_buffer)
            executed = sum(1 for p in self.trajectory_buffer if p['executed'])
            return {
                'total_points': total,
                'executed_points': executed,
                'pending_points': total - executed,
                'buffer_full': total >= self.buffer_size
            }

# Usage example in main robot code:
def main_hybrid_approach():
    # Initialize hybrid follower
    trajectory_follower = HybridTrajectoryFollower(buffer_size=50)
    
    # Thread 1: Read from ROS bridge and buffer points
    def ros_reader_thread():
        while True:
            # Read from JSON file
            try:
                with open('/tmp/joint_states.json', 'r') as f:
                    data = json.load(f)
                
                trajectory_follower.add_trajectory_point(
                    data['joint_positions'],
                    data['joint_names'],
                    data['timestamp']
                )
                
            except Exception as e:
                print(f"Error reading ROS data: {e}")
                
            time.sleep(0.02)  # 50Hz reading
    
    # Thread 2: Execute commands at controlled rate
    def robot_execution_thread():
        while True:
            positions, joint_names = trajectory_follower.get_next_command()
            
            if positions and joint_names:
                # Execute on real robot
                print(f"Executing: {[f'{p:.1f}°' for p in positions]}")
                # robot.move_abs_with_speed(positions, speed=MAX_SPEED)
                
                # Show buffer status
                status = trajectory_follower.get_buffer_status()
                print(f"Buffer: {status['pending_points']}/{status['total_points']} pending")
                
            time.sleep(0.05)  # 20Hz execution
    
    # Start both threads
    threading.Thread(target=ros_reader_thread, daemon=True).start()
    threading.Thread(target=robot_execution_thread, daemon=True).start()

if __name__ == '__main__':
    main_hybrid_approach()
