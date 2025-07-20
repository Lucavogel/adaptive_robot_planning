#!/usr/bin/env python3
"""
Simple test: move a little, come back to home, move again.
Adapted for Lynx SES900 robot with main_sim_ros_bridge_hybrid.py
No offset, home is [0,0,0,0,0,0]
"""

import json
import time
import os

def write_lynx_move_test():
    """Write simple move and return to home test for Lynx SES900 robot."""
    
    data_file = '/tmp/moveit_to_pybullet_data.json'
    
    # Simple test: move → home → move → home
    # Using realistic angles for Lynx SES900 robot
    test_positions = [
        # Position 1: Home position
        {
            'positions': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Home position'
        },
        # Position 2: Small base rotation
        {
            'positions': [30.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Base rotation 30°'
        },
        # Position 3: Back to home
        {
            'positions': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Back to home'
        },
        # Position 4: Small shoulder movement
        {
            'positions': [0.0, -30.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Shoulder movement -30°'
        },
        # Position 5: Back to home
        {
            'positions': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Back to home'
        },
        # Position 6: Small elbow movement
        {
            'positions': [0.0, 0.0, 45.0, 0.0, 0.0, 0.0],
            'description': 'Elbow 45°'
        },
        # Position 7: Multi-joint movement
        {
            'positions': [15.0, -20.0, 30.0, -15.0, 20.0, 0.0],
            'description': 'Multi-joint position'
        },
        # Position 8: Final home
        {
            'positions': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'description': 'Final home'
        }
    ]
    
    # Joint names for Lynx SES900 robot (as used in main_sim_ros_bridge_hybrid.py)
    joint_names = [
        'joint_1',  # Base rotation
        'joint_2',  # Shoulder
        'joint_3',  # Upper arm
        'joint_4',  # Forearm
        'joint_5',  # Wrist
        'joint_6'   # End-effector rotation
    ]
    
    print("🤖 Starting Lynx SES900 simple move test...")
    print(f"📁 Writing test positions to: {data_file}")
    print("💡 Pattern: move → home → move → home")
    print("   Home position: [0,0,0,0,0,0]")
    print("   Robot: Lynx SES900")
    print("   Bridge: main_sim_ros_bridge_hybrid.py")
    print("")
    
    try:
        for i, test_pos in enumerate(test_positions):
            print(f"📍 Position {i+1}: {test_pos['description']}")
            print(f"   Joints: {[f'{pos:.1f}°' for pos in test_pos['positions']]}")
            
            # Create JSON data compatible with main_sim_ros_bridge_hybrid.py
            data = {
                'timestamp': time.time(),
                'joint_positions': test_pos['positions'],
                'joint_names': joint_names,
                'robot_model': 'lynx_ses900',
                'move_type': 'position_control'
            }
            
            # Write to file
            with open(data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"   ✅ Written to {data_file}")
            
            # Wait for robot to move
            wait_time = 5  # Longer wait time for smoother movements
            print(f"   ⏱️  Waiting {wait_time} seconds for robot to move...")
            time.sleep(wait_time)
            print("")
            
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user.")
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    print("✅ Lynx SES900 simple move test completed!")
    print("💡 Robot should have done:")
    print("   - Base rotation 30° → home")
    print("   - Shoulder movement -30° → home") 
    print("   - Elbow movement 45° → home")
    print("   - Multi-joint position → home")
    print("")
    print("🔧 To run this test:")
    print("   1. Start the hybrid bridge: python real_robot/main_sim_ros_bridge_hybrid.py")
    print("   2. In another terminal: python test_lynx_movements.py")

def verify_bridge_data_format():
    """Verify that the data format is compatible with the hybrid bridge."""
    data_file = '/tmp/moveit_to_pybullet_data.json'
    
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            print("📋 Current bridge data format:")
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"   Joint names: {data.get('joint_names', [])}")
            print(f"   Joint positions: {data.get('joint_positions', [])}")
            print(f"   Robot model: {data.get('robot_model', 'N/A')}")
            return True
        except Exception as e:
            print(f"❌ Error reading bridge data: {e}")
            return False
    else:
        print(f"📁 Bridge data file not found: {data_file}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Lynx SES900 Movement Test")
    print("=" * 60)
    
    # Check if bridge data file exists and show current format
    print("🔍 Checking bridge data format...")
    verify_bridge_data_format()
    print("")
    
    # Run the movement test
    write_lynx_move_test()
