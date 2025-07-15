# test_joint_watchdog.py

import robot
from safety import JointLimitWatchdog
import time

# --- SETUP ---
print("--- Initializing Robot ---")
robo = robot.Robot(portname='/dev/ttyACM0')
if not robo.init_bus():
    print("Failed to initialize bus. Exiting.")
    exit()
robo.init_motors()

# --- DEFINE JOINT LIMITS ---
# Define the safe operating range [min_angle, max_angle] for each of the 6 joints.
# These values are in degrees.
# Let's say Joint 3 (the 4th motor) has a very restrictive limit for our test.
# Use a very large number like 9999 for joints with no practical limit.
JOINT_LIMITS = [
    (-1, 1),  # Joint 0
    (-1, 1),    # Joint 1
    (-1, 1),    # Joint 2
    (-40, 40),    # Joint 3 <- The one we will violate
    (-40, 40),  # Joint 4
    (-40, 40),  # Joint 5
]

# --- INITIALIZE AND START THE WATCHDOG ---
print("\n--- Starting Joint Limit Watchdog ---")
# Create an instance of the watchdog
joint_watchdog = JointLimitWatchdog(robot_controller=robo, joint_limits=JOINT_LIMITS)

# Attach it to the robot object for clean shutdown via atexit
robo.joint_watchdog = joint_watchdog

# Start monitoring in the background
joint_watchdog.start()


print("\n--- Phase 1: Safe Moves ---")
print("Moving robot within defined joint limits. Watchdog should not trigger.")

# Start at a known safe position
safe_pos = [0, 0, 0, 0, 0, 0]
print(f"Moving to safe home position: {safe_pos}")
robo.move_abs(safe_pos)
time.sleep(2)

# Move to another safe position
safe_pos_2 = [0, 0, 0, 10, 10, 10]
print(f"Moving to another safe position: {safe_pos_2}")
robo.move_abs(safe_pos_2)
time.sleep(2) # Give it time to move and for the watchdog to check


print("\n--- Phase 2: Attempting a Dangerous Move ---")
# This position violates the limit for Joint 3, which is max 45 degrees.
dangerous_pos = [0, 0, 0, 50, 0, 0]
print(f"Sending DANGEROUS command to move Joint 3 to {dangerous_pos[3]} degrees.")
print(f"(Limit for Joint 3 is {JOINT_LIMITS[3][1]} degrees)")

robo.move_abs(dangerous_pos)

# The robot will start moving towards the dangerous position.
# The watchdog thread runs in the background, continuously checking the arm's
# actual reported position. As soon as get_Position() reports a value > 45
# for joint 3, the watchdog will trigger the LIMP command.
print("\nWaiting for watchdog to trigger...")
time.sleep(3) # Give it plenty of time for the arm to move and the watchdog to react.


print("\n--- Test Complete ---")
print("The robot arm should now be in a 'LIMP' state.")
# The robo.shutdown() method (registered with atexit) will automatically
# stop the watchdog thread and close the serial bus.