#!/usr/bin/env python3
"""
Simple test: move a little, come back to home, move again.
No offset, home is [0,0,0,0,0,0]
"""

import json
import time
import os

def write_simple_move_test():
    """Write simple move and return to home test."""
    
    data_file = '/tmp/moveit_to_pybullet_data.json'
    
    # Simple test: move → home → move → home
    test_positions = [
        # Position 1: Home position
        {
            'positions': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Home position'
        },
        # Position 2: Small base rotation
        {
            'positions': [0, 0, 0.0, 0.0, 20, 0.0],
            'description': 'Base rotation 20°'
        },
        # Position 3: Back to home
        {
            'positions': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Back to home'
        },
        # Position 4: Small shoulder movement
        {
            'positions': [0, 0, 0.0, 0.0, -20, 0.0],
            'description': 'Shoulder up 15°'
        },
        # Position 5: Back to home
        {
            'positions': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Back to home'
        },
        # Position 6: Small elbow movement
        {
            'positions': [0.0, 0.0, 0, 0, 0.0, 20],
            'description': 'Elbow 20°'
        },
        # Position 7: Final home
        {
            'positions': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Final home'
        }
    ]
    
    joint_names = [
        'joint_1',  # Base rotation
        'joint_2',  # Shoulder
        'joint_3',  # Upper arm
        'joint_4',  # Forearm
        'joint_5',  # Wrist 
        'joint_6'   # End-effector rotation
    ]
    
    print("🤖 Starting simple move test...")
    print(f"📁 Writing test positions to: {data_file}")
    print("💡 Pattern: move → home → move → home")
    print("   Home position: [0,0,0,0,0,0]")
    print("")
    
    try:
        for i, test_pos in enumerate(test_positions):
            print(f"📍 Position {i+1}: {test_pos['description']}")
            print(f"   Joints: {[f'{pos:.1f}°' for pos in test_pos['positions']]}")
            
            # Create JSON data
            data = {
                'timestamp': time.time(),
                'joint_positions': test_pos['positions'],
                'joint_names': joint_names
            }
            
            # Write to file
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"   ✅ Written to {data_file}")
            
            # Wait for robot to move
            wait_time = 4
            print(f"   ⏱️  Waiting {wait_time} seconds for robot to move...")
            time.sleep(wait_time)
            print("")
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user.")
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    print("✅ Simple move test completed!")
    print("💡 Robot should have done:")
    print("   - Base rotation → home")
    print("   - Shoulder up → home") 
    print("   - Elbow movement → home")

if __name__ == '__main__':
    write_simple_move_test()
