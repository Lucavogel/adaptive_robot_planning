import time
import random
from robot import Robot
from safety import JointLimitWatchdog

if __name__ == '__main__':
    # --- SETUP ROBOT & WATCHDOG ---
    PORT = '/dev/ttyACM0'
    robo = Robot(portname=PORT)
    if not robo.init_bus():
        print("Failed to open serial port. Exiting.")
        exit(1)
    robo.init_motors()

    # Define joint limits exactly as in your real use case
    JOINT_LIMITS = [
        (-1,   1),    # Joint 0
        (-1,   1),    # Joint 1
        (-1,   1),    # Joint 2
        (-40, 40),    # Joint 3  <-- the “tight” one
        (-40, 40),    # Joint 4
        (-40, 40),    # Joint 5
    ]

    watchdog = JointLimitWatchdog(robot_controller=robo,
                                  joint_limits=JOINT_LIMITS)
    robo.joint_watchdog = watchdog    # so robo.shutdown() will clean it up
    watchdog.start()

    # --- RANDOM COMMAND LOOP ---
    ITERS = 2000        # max number of random commands
    INTERVAL = 0.5     # seconds between commands (i.e. 2 Hz)

    print(f"Starting random‐stress test: up to {ITERS} commands @ {1/INTERVAL:.1f} Hz...")
    for i in range(ITERS):
        # pick a random joint index
        j = random.randrange(len(JOINT_LIMITS))
        min_l, max_l = JOINT_LIMITS[j]
        # expand range by 50% so we sometimes go outside the limit
        span = max(abs(min_l), abs(max_l)) * 1.5
        angle = random.uniform(-span, span)

        # construct a 6‐element command (only joint j moves)
        cmd = [0.0]*len(JOINT_LIMITS)
        cmd[j] = angle

        print(f"[{i+1}/{ITERS}] -> move_abs: joint {j} → {angle:.1f}°")
        robo.move_abs(cmd)

        # give the robot & watchdog some time
        time.sleep(INTERVAL)

    print("Test loop complete. Cleaning up...")
    robo.shutdown()
    print("All done.")