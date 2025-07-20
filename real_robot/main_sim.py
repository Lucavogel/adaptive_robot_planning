# numpy, scipy, pyserial, pybullet.
import logging
import numpy as np
import time
import random
import threading

from sim_robot import SimRobot
from safety import SafetyWatchdogSim
from sim_sensor import SimNatNetDataHandler
import rl_config # Import the configuration file

if __name__ == '__main__':
    robo = SimRobot() # Use the new API for SimRobot's __init__
    if not robo.init_bus(): # init_bus now handles PyBullet connection and robot loading
        print("[Main] Failed to open simulation. Exiting.")
        exit(1)
    robo.init_motors()

    # Get PyBullet related info using new getter methods
    pybullet_api = robo.get_pybullet_api()
    physics_client_id = robo.get_physics_client_id()
    robot_id = robo.get_robot_id()
    ee_link_id = robo.get_end_effector_link_id()
    pybullet_api_lock = robo.get_pybullet_api_lock()

    sim_data_manager = SimNatNetDataHandler(
            p_api=pybullet_api,
            physics_client_id=physics_client_id,
            robot_id=robot_id,
            end_effector_link_id=ee_link_id,
            pybullet_api_lock=pybullet_api_lock, # PASS THE NEW GLOBAL LOCK
            verbose=False
        )
    # natnet_client_thread = threading.Thread(target=run_natnet_client_in_thread,
    #                                         args=(natnet_data_manager, rl_config.NATNET_SERVER_IP),
    #                                         daemon=True)
    # natnet_client_thread.start()
    print("[Main] Waiting for NatNet client to connect and receive initial data (max 10s)...")
    connect_timeout = rl_config.NATNET_CONNECT_TIMEOUT
    start_time = time.time()

    print("[Main] Simulated sensor initialized.")  # There is no need for checking the connection in simulation sensors

    watchdog = SafetyWatchdogSim(
        robot_controller=robo,
        natnet_data_handler=sim_data_manager,
        joint_limits=rl_config.JOINT_LIMITS,
        marker_radii=rl_config.MARKER_RADII,
    )
    robo.joint_watchdog = watchdog
    watchdog.start(check_interval=rl_config.WATCHDOG_INTERVAL)

    print(f"[Main] Starting random stress test: up to {rl_config.STRESS_TEST_ITERS} commands @ {1/rl_config.STRESS_TEST_INTERVAL:.1f} Hz...")
    stress_test_iters = 0
    # PyBullet's default physics delta time is 1/240th of a second
    sim_steps_per_interval = int(rl_config.STRESS_TEST_INTERVAL / (1.0/240.0))
    # Ensure at least one step is taken
    sim_steps_per_interval = max(1, sim_steps_per_interval)
    try:
        while stress_test_iters < rl_config.STRESS_TEST_ITERS:
            for i in range(sim_steps_per_interval):
                if watchdog._exception_event.is_set():
                    print("\n[Main] Watchdog thread reported a critical exception. Stopping main loop.")
                    robo.enter_emergency_recovery()
                    break

                if i == 0:
                    cmd = []
                    for j_idx, (min_l, max_l) in enumerate(rl_config.JOINT_LIMITS):
                        # Generate random angle, then clamp it to actual joint limits
                        span = max(abs(min_l), abs(max_l)) * 1.5
                        angle = random.uniform(-span, span)
                        # Clamp the angle to stay within the joint limits defined in rl_config.py
                        clamped_angle = np.clip(angle, min_l, max_l)
                        cmd.append(clamped_angle)

                    # cmd = [12., 0., 90., 0., 0., 0.]  # Example command for testing

                    # TODO: develop a thread/ROS node to transfer the joint angle topic to the 'cmd' var.
                    print(f"[Main] [{i+1}/{rl_config.STRESS_TEST_ITERS}] -> move_abs: {cmd}")
                    robo.move_abs_with_speed(cmd, speed=rl_config.MAX_SPEED)
                    stress_test_iters += 1

                    if sim_data_manager.latest_relative_pos is not None:
                        print(f'[Main] eef relative pos X={sim_data_manager.latest_relative_pos[0]:.4f}, Y={sim_data_manager.latest_relative_pos[1]:.4f}, Z={sim_data_manager.latest_relative_pos[2]:.4f}')
                    else:
                        print('[Main] eef relative pos: Data not available.')

                    # --- ADDED LOGGING ---
                    current_joint_angles = robo.get_Position()
                    if current_joint_angles:
                        print(f"[Main] Current Joint Angles (deg): {[f'{angle[0]:.2f}' if angle[0] is not None else 'N/A' for angle in current_joint_angles]}")
                    # ---------------------

                with pybullet_api_lock: # Ensure thread safety for PyBullet API calls
                    pybullet_api.stepSimulation(physicsClientId=physics_client_id)
                # Introduce a small sleep to yield control and prevent busy-waiting
                time.sleep(0.001)


        print("[Main] Test loop complete.")
    except KeyboardInterrupt:
        print("\n[Main] CTRL-C detected. Initiating emergency recovery...")
        robo.enter_emergency_recovery()
    except Exception as e:
        print(f"[Main] Main loop exception found: {e}. Initiating emergency recovery...")
        robo.enter_emergency_recovery()
    finally:
        print("[Main] Cleaning up resources...")
        robo.shutdown()
        print("[Main] All done.")
