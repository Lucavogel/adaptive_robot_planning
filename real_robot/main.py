import logging
import numpy as np
import time
import random
import threading

from robot import Robot
from safety import SafetyWatchdog
from optitrack import NatNetDataHandler, run_natnet_client_in_thread
import rl_config # Import the configuration file

if __name__ == '__main__':
    robo = Robot(portname=rl_config.PORT)
    if not robo.init_bus():
        print("[Main] Failed to open serial port. Exiting.")
        exit(1)
    robo.init_motors()

    natnet_data_manager = NatNetDataHandler(verbose=False)
    natnet_client_thread = threading.Thread(target=run_natnet_client_in_thread,
                                            args=(natnet_data_manager, rl_config.NATNET_SERVER_IP),
                                            daemon=True)
    natnet_client_thread.start()
    print("[Main] Waiting for NatNet client to connect and receive initial data (max 10s)...")
    connect_timeout = rl_config.NATNET_CONNECT_TIMEOUT
    start_time = time.time()
    while not natnet_data_manager.is_connected and (time.time() - start_time < connect_timeout):
        time.sleep(0.5)
    
    if not natnet_data_manager.is_connected:
        print("[Main] NatNet client failed to connect within timeout. Proceeding without OptiTrack data.")
    else:
        print("[Main] NatNet client connected and received initial data.")

    watchdog = SafetyWatchdog(
        robot_controller=robo,
        natnet_data_handler=natnet_data_manager,
        joint_limits=rl_config.JOINT_LIMITS,
        marker_radii=rl_config.MARKER_RADII,
    )
    robo.joint_watchdog = watchdog
    watchdog.start(check_interval=rl_config.WATCHDOG_INTERVAL)

    print(f"[Main] Starting random stress test: up to {rl_config.STRESS_TEST_ITERS} commands @ {1/rl_config.STRESS_TEST_INTERVAL:.1f} Hz...")

    try:
        for i in range(rl_config.STRESS_TEST_ITERS):
            if watchdog._exception_event.is_set():
                print("\n[Main] Watchdog thread reported a critical exception. Stopping main loop.")
                robo.enter_emergency_recovery()
                break

            cmd = []
            for j_idx, (min_l, max_l) in enumerate(rl_config.JOINT_LIMITS):
                span = max(abs(min_l), abs(max_l)) * 1.5
                angle = random.uniform(-span, span)
                cmd.append(angle)

            print(f"[Main] [{i+1}/{rl_config.STRESS_TEST_ITERS}] -> move_abs: {cmd}")
            robo.move_abs_with_speed(cmd, speed=rl_config.MAX_SPEED)
            if natnet_data_manager.latest_relative_pos is not None:
                print(f'[Main] eef relative pos X={natnet_data_manager.latest_relative_pos[0]:.4f}, Y={natnet_data_manager.latest_relative_pos[1]:.4f}, Z={natnet_data_manager.latest_relative_pos[2]:.4f}')
            else:
                print('[Main] eef relative pos: Data not available.')

            time.sleep(rl_config.STRESS_TEST_INTERVAL)

        print("[Main] Test loop complete.")
    except KeyboardInterrupt:
        print("\n[Main] CTRL-C detected. Initiating emergency recovery...")
        robo.enter_emergency_recovery()
    except Exception as e:
        print(f"[Main] Main loop exception found. Initiating emergency recovery...")
        robo.enter_emergency_recovery()
    finally:
        print("[Main] Cleaning up resources...")
        robo.shutdown()
        print("[Main] All done.")
