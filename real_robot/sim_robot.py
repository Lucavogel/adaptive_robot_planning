# File: sim_robot.py

import os
import pybullet as p  # Keep this import as p
import pybullet_data
import time
import threading
import numpy as np
import subprocess
import tempfile
import logging
import numpy as np
import time
import random
import threading

from robot import Robot
from safety import SafetyWatchdog
from optitrack import NatNetDataHandler, run_natnet_client_in_thread
import rl_config # Import the configuration file


# Mimic motor_cmd constants needed by Robot class.
class LSSConstants:
    LSS_BroadcastID = 254


lssc = LSSConstants()


# --- MODIFICATION START ---
# A. Modify SimMotor to accept and use the pybullet module API and client ID
class SimMotor:
    def __init__(self, id, robot_id, p_api, physics_client_id, joint_id, bus_lock, pybullet_api_lock):
        self._id = id
        self._robot_id = robot_id
        self._p_api = p_api
        self._physics_client_id = physics_client_id
        self._joint_id = joint_id
        self._bus_lock = bus_lock
        self._pybullet_api_lock = pybullet_api_lock

        self._target_position_rad = 0.0

    def genericRead_Blocking_int(self, cmd):
        if cmd == "QD":
            # with self._bus_lock:
            with self._pybullet_api_lock:
                joint_state = self._p_api.getJointState(self._robot_id, self._joint_id, physicsClientId=self._physics_client_id)
            return int(np.degrees(joint_state[0]) * 100)
        return None

    # Generic write/read are simplified as they won't send/receive actual serial data
    def genericWrite(self, cmd, param=None):
        pass

    def reset(self):
        pass

    def limp(self):
        # with self._bus_lock:
        with self._pybullet_api_lock:
            self._p_api.setJointMotorControl2(
                bodyUniqueId=self._robot_id,
                jointIndex=self._joint_id,
                controlMode=self._p_api.VELOCITY_CONTROL,
                targetVelocity=0,
                force=0,
                physicsClientId=self._physics_client_id
            )

    def hold(self):
        # with self._bus_lock:
        current_pos = self.getPosition()
        if current_pos is not None:
            with self._pybullet_api_lock:
                current_pos_rad = np.radians(current_pos / 100.0)
                self._p_api.setJointMotorControl2(
                    bodyIndex=self._robot_id,
                    jointIndex=self._joint_id,
                    controlMode=self._p_api.POSITION_CONTROL,
                    targetPosition=current_pos_rad,
                    force=500,  # kp=0.5, kd=0.05,
                    physicsClientId=self._physics_client_id
                )

    def move_abs(self, pos_centi_deg):
        # with self._bus_lock:
        with self._pybullet_api_lock:
            target_pos_rad = np.radians(pos_centi_deg / 100.0)
            self._target_position_rad = target_pos_rad
            self._p_api.setJointMotorControl2(
                bodyUniqueId=self._robot_id,
                jointIndex=self._joint_id,
                controlMode=self._p_api.POSITION_CONTROL,
                targetPosition=target_pos_rad,
                maxVelocity=10,
                physicsClientId=self._physics_client_id
            )

    def move_abs_with_speed(self, pos_centi_deg, speed):
        # with self._bus_lock:
        with self._pybullet_api_lock:
            target_pos_rad = np.radians(pos_centi_deg / 100.0)
            self._target_position_rad = target_pos_rad
            pybullet_max_velocity = (speed / 1000.0) * 15
            pybullet_max_velocity = max(0.1, pybullet_max_velocity)
            self._p_api.setJointMotorControl2(
                bodyUniqueId=self._robot_id,
                jointIndex=self._joint_id,
                controlMode=self._p_api.POSITION_CONTROL,
                targetPosition=target_pos_rad,
                maxVelocity=pybullet_max_velocity,
                physicsClientId=self._physics_client_id
            )

    def getPosition(self):
        return self.genericRead_Blocking_int("QD")


# B. Modify SimRobot to store and pass around the pybullet module and client ID
class SimRobot:
    def __init__(self, render_mode, emergency_time=0.5):
        self.render_mode = render_mode
        self._pybullet_api = p

        self._pybullet_api_lock = threading.Lock() # NEW: CREATE the global PyBullet API lock

        with self._pybullet_api_lock: # ACQUIRE LOCK for p.connect
            self._physics_client = self._pybullet_api.connect(self._pybullet_api.GUI if self.render_mode == "human" else self._pybullet_api.DIRECT)
            self._pybullet_api.setAdditionalSearchPath(pybullet_data.getDataPath())
            self._pybullet_api.setGravity(0, 0, -9.81)

        self._bus = True
        self._bus_lock = threading.Lock() # This lock is specifically for motor access, NOT for PyBullet API calls
        self._motor_ids = [0, 1, 2, 3, 4, 5]
        self._motors = []
        self._robot_id = None
        self.home_position = [0, 0, 0, 0, 0, 0]
        self._joint_info = []
        self._end_effector_link_id = -1
        self._in_emergency_state = False
        self._emergency_thread = None
        self._emergency_time = emergency_time  # Time in seconds for emergency recovery

        # --- IMPORTANT CHANGE 1: Initialize the attribute here ---
        self._controlled_joint_indices = []

        # --- IMPORTANT CHANGE 2: Call init_bus here to populate _controlled_joint_indices ---
        if not self.init_bus():
            raise RuntimeError("Failed to initialize simulated robot in PyBullet. Check URDF/Xacro paths and files.")

    def init_bus(self):
        print("[SimRobot] Initializing PyBullet client and loading robot...")
        try:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            urdf_load_path = os.path.join(current_script_dir, "ur5.urdf")

            if not os.path.exists(urdf_load_path):
                raise FileNotFoundError(f"URDF file not found at: {urdf_load_path}")

            with self._pybullet_api_lock:
                self._pybullet_api.setAdditionalSearchPath(current_script_dir)

            with self._pybullet_api_lock: # ACQUIRE LOCK for loadURDF
                URDF_SPAWN_HEIGHT = 0.0  # Example value, adjust as needed

                self._robot_id = self._pybullet_api.loadURDF(
                    urdf_load_path,
                    [0, 0, URDF_SPAWN_HEIGHT],
                    useFixedBase=True,
                    physicsClientId=self._physics_client
                )
            # REMOVE or COMMENT OUT the following lines:
            # if temp_urdf_path and os.path.exists(temp_urdf_path):
            #     os.remove(temp_urdf_path)
            #     print(f"[SimRobot] Cleaned up temporary URDF: {temp_urdf_path}")

            with self._pybullet_api_lock: # ACQUIRE LOCK for getNumJoints, getJointInfo
                num_joints = self._pybullet_api.getNumJoints(self._robot_id, physicsClientId=self._physics_client)
                controlled_joint_indices = []
                for i in range(num_joints):
                    info = self._pybullet_api.getJointInfo(self._robot_id, i, physicsClientId=self._physics_client)
                    joint_name = info[1].decode("utf-8")
                    joint_type = info[2]
                    if joint_type == self._pybullet_api.JOINT_REVOLUTE:
                        controlled_joint_indices.append(i)
                self._controlled_joint_indices = controlled_joint_indices[:6]
                if len(self._controlled_joint_indices) != 6:
                    print(f"[SimRobot] Warning: Expected 6 controlled joints for UR5-like arm, found {len(self._controlled_joint_indices)}.")

                self._end_effector_link_id = -1
                for i in range(num_joints):
                    info = self._pybullet_api.getJointInfo(self._robot_id, i, physicsClientId=self._physics_client)
                    link_name = info[12].decode("utf-8")
                    if "tool0" in link_name or "ee_link" in link_name or "wrist_3_link" in link_name:
                        self._end_effector_link_id = i
                        print(f"[SimRobot] Identified End-Effector Link: {link_name} (PyBullet Link ID: {i})")
                        break
                if self._end_effector_link_id == -1:
                    print("[SimRobot] Warning: Could not find specific end-effector. Using default fallback.")
                    self._end_effector_link_id = self._controlled_joint_indices[-1] if self._controlled_joint_indices else 0

            print(f"[SimRobot] Robot loaded with PyBullet ID: {self._robot_id}")
            print(f"[SimRobot] Controlled PyBullet Joint IDs (mapped to LSS IDs 0-5): {self._controlled_joint_indices}")

            with self._pybullet_api_lock: # ACQUIRE LOCK for stepSimulation
                self._pybullet_api.stepSimulation(physicsClientId=self._physics_client)
            if self.render_mode == "human":
                time.sleep(0.1)
            return True
        except Exception as e:
            print(f"[SimRobot] Error during robot loading/initialization: {e}")
            self._bus = False
            return False

    def close_bus(self):
        if self._physics_client is not None:
            with self._pybullet_api_lock: # ACQUIRE LOCK for disconnect
                self._pybullet_api.disconnect(self._physics_client)
            print("[SimRobot] Disconnected from PyBullet.")
            self._physics_client = None
            self._bus = False

    def init_motors(self):
        if not self._bus:
            print("[SimRobot] Bus not initialized, cannot initialize motors.")
            return None
        self._motors = []
        for i, joint_idx in enumerate(self._controlled_joint_indices):
            m = SimMotor(id=self._motor_ids[i], robot_id=self._robot_id,
                         p_api=self._pybullet_api, physics_client_id=self._physics_client,
                         joint_id=joint_idx, bus_lock=self._bus_lock, # Pass _bus_lock
                         pybullet_api_lock=self._pybullet_api_lock) # PASS THE NEW GLOBAL LOCK
            self._motors.append(m)
        print(f"[SimRobot] Initialized {len(self._motors)} simulated motors.")

    def get_Position(self):
        pos_all_raw = []
        for m in self._motors:
            raw = m.getPosition()
            if raw is None:
                pos_all_raw.append(None)
                continue
            deg = float(raw) / 100.0
            pos_all_raw.append(deg)

        valid_positions = [p for p in pos_all_raw if p is not None]
        if len(valid_positions) == len(self._motor_ids):
            self._current_joint_angles_deg = valid_positions
        else:
            print(
                "[SimRobot] Warning: Not all joint positions could be read. _current_joint_angles_deg not updated this cycle.")

        return [[p] if p is not None else [None] for p in pos_all_raw]

    def move_abs(self, action_degrees):
        if self._in_emergency_state:
            print("[SimRobot] In emergency state, ignoring move_abs() command.")
            return

        action_degrees = list(action_degrees)
        assert len(action_degrees) == len(self._motors)

        for idx, target_deg in enumerate(action_degrees):
            target_centi_deg = int(target_deg * 100)
            self._motors[idx].move_abs(target_centi_deg)

    def move_abs_admin(self, action_degrees):
        # Skip the emergency state check for admin commands
        action_degrees = list(action_degrees)
        assert len(action_degrees) == len(self._motors)

        for idx, target_deg in enumerate(action_degrees):
            target_centi_deg = int(target_deg * 100)
            self._motors[idx].move_abs(target_centi_deg)

    def move_abs_with_speed(self, action_degrees, speed):
        if self._in_emergency_state:
            print("[SimRobot] In emergency state, ignoring move_abs_with_speed() command.")
            return

        action_degrees = list(action_degrees)
        assert len(action_degrees) == len(self._motors)

        for idx, target_deg in enumerate(action_degrees):
            target_centi_deg = int(target_deg * 100)
            self._motors[idx].move_abs_with_speed(target_centi_deg, speed)

    def move_abs_with_speed_admin(self, action_degrees, speed):
        # Skip the emergency state check for admin commands
        action_degrees = list(action_degrees)
        assert len(action_degrees) == len(self._motors)

        for idx, target_deg in enumerate(action_degrees):
            target_centi_deg = int(target_deg * 100)
            self._motors[idx].move_abs_with_speed(target_centi_deg, speed)

    def limp(self):
        for m in self._motors:
            m.limp()
        print("[SimRobot] All simulated motors in limp mode.")

    def hold(self):
        for m in self._motors:
            m.hold()
        print("[SimRobot] All simulated motors in hold mode.")

    def limp_broadcast(self):
        self.limp()

    def hold_broadcast(self):
        self.hold()

    def enter_emergency_recovery(self):
        if self._in_emergency_state:
            return

        self._in_emergency_state = True
        # self._emergency_thread = threading.Thread(target=self._emergency_recovery_task, daemon=True)
        # self._emergency_thread.start()

        self._emergency_recovery_task()

    def _emergency_recovery_task(self):
        print("\n" + "=" * 40)
        print("! ! ! SIM ROBOT ENTERING EMERGENCY RECOVERY ! ! !")
        print("[Emergency] Holding all joints...")
        self.hold()
        time.sleep(self._emergency_time)

        print(f"[Emergency] Moving to safe home position: {self.home_position}")
        self._move_and_wait_admin(self.home_position, sim_steps_per_check=50)

        # NEW: Print after the move_and_wait attempt
        print("[Emergency] _move_and_wait in recovery finished (may have timed out).")

        # NEW: Get the current EEF position *after* the recovery move
        # To get the latest EEF position, you'd need safe access to the sensor manager.
        # This is a bit tricky from here without passing it around, but you can rely on the
        # SimNatNetDataHandler to be updated by the next _get_obs() call.
        # For now, we trust _move_and_wait to attempt the move.

        self._in_emergency_state = False  # This flag MUST be set to False for the loop to exit
        print(
            "[Emergency] Home position reached. Resuming normal operation.")  # This means _in_emergency_state is set to False
        print("=" * 40 + "\n")
        print("[Emergency] Recovery task completed (`_in_emergency_state` is now False).")

    def _move_and_wait(self, target_position_degrees, tolerance=2.0, sim_steps_per_check=20):
        self.move_abs(target_position_degrees) # This sends commands using SimMotor, which uses the lock

        timeout_steps = 1000
        current_sim_steps = 0

        while not self._is_at_target(target_position_degrees, tolerance=tolerance):
            with self._pybullet_api_lock: # ACQUIRE LOCK for stepSimulation
                self._pybullet_api.stepSimulation(physicsClientId=self._physics_client)
            current_sim_steps += 1
            if current_sim_steps >= timeout_steps:
                print(f"[SimRobot] Warning: _move_and_wait timed out after {timeout_steps} steps before reaching target.")
                break
            if current_sim_steps % sim_steps_per_check == 0:
                time.sleep(0.001)

    def _move_and_wait_admin(self, target_position_degrees, tolerance=2.0, sim_steps_per_check=20):
        self.move_abs_with_speed_admin(target_position_degrees, speed=0.1) # This sends commands using SimMotor, which uses the lock

        timeout_steps = 1000
        current_sim_steps = 0

        while not self._is_at_target(target_position_degrees, tolerance=tolerance):
            with self._pybullet_api_lock: # ACQUIRE LOCK for stepSimulation
                self._pybullet_api.stepSimulation(physicsClientId=self._physics_client)
            current_sim_steps += 1
            if current_sim_steps >= timeout_steps:
                print(f"[SimRobot] Warning: _move_and_wait timed out after {timeout_steps} steps before reaching target.")
                break
            if current_sim_steps % sim_steps_per_check == 0:
                time.sleep(0.001)


    def _is_at_target(self, target_position_degrees, tolerance=2.0):
        current_pos_list = self.get_Position()
        current_pos = [p[0] for p in current_pos_list if p[0] is not None]

        if len(current_pos) != len(target_position_degrees):
            print(
                f"[SimRobot._is_at_target] Mismatch in joint count. Current: {len(current_pos)}, Target: {len(target_position_degrees)}")
            return False

        max_diff = 0.0
        for i in range(len(target_position_degrees)):
            diff = abs(current_pos[i] - target_position_degrees[i])
            max_diff = max(max_diff, diff)
            if diff > tolerance:
                # Uncomment the line below temporarily to see which joint is off
                # print(f"[SimRobot._is_at_target] Joint {i} (Current: {current_pos[i]:.2f} deg) != (Target: {target_position_degrees[i]:.2f} deg) by {diff:.2f} deg (Tol: {tolerance:.2f})")
                return False
        # Uncomment the line below if _is_at_target returns True
        # print(f"[SimRobot._is_at_target] All joints within tolerance. Max diff: {max_diff:.2f} deg")
        return True

    def shutdown(self):
        print("[SimRobot] Shutting down simulation...")
        if self._emergency_thread and self._emergency_thread.is_alive():
            print("[SimRobot] Waiting for active emergency recovery to complete before shutting down PyBullet...")
            self._emergency_thread.join()
            self._in_emergency_state = False
        self.close_bus()
        print("[SimRobot] Shutdown complete.")

    def get_info(self):
        # Now returns the pybullet_api_lock too
        return self._pybullet_api, self._physics_client, self._robot_id, self._end_effector_link_id, self._pybullet_api_lock

    def draw_debug_sphere(self, position, radius=0.02, color=[1, 0, 0, 1], life_time=0):
        """
        Draws a debug sphere in the PyBullet simulation.
        :param position: [x, y, z] coordinates of the sphere center.
        :param radius: Radius of the sphere.
        :param color: RGBA color tuple (e.g., [1, 0, 0, 1] for red).
        :param life_time: How long the sphere should be visible (0 for persistent).
        """
        with self._pybullet_api_lock:
            # Create a visual shape (sphere)
            visual_shape_id = self._pybullet_api.createVisualShape(
                shapeType=self._pybullet_api.GEOM_SPHERE,
                radius=radius,
                rgbaColor=color,
                physicsClientId=self._physics_client
            )
            # Create a body (object) using the visual shape
            # No collision shape needed for a purely visual marker
            sphere_body_id = self._pybullet_api.createMultiBody(
                baseVisualShapeIndex=visual_shape_id,
                basePosition=position,
                physicsClientId=self._physics_client
            )
            # PyBullet debug lines/points are usually more transient.
            # For a persistent object, createMultiBody is better.
            # If life_time is not 0, we might need to manage these objects.
            # For simplicity, we'll assume persistent for now or rely on reset.
            # For transient, use self._pybullet_api.addUserDebugLine or addUserDebugText
            # self._pybullet_api.addUserDebugText(
            #     text="Target",
            #     textPosition=position,
            #     textColorRGB=[1, 0, 0],
            #     lifeTime=life_time,
            #     physicsClientId=self._physics_client
            # )
        return sphere_body_id

    def change_sphere_color(self, object_id, color):
        """
        Changes the RGBA color of an existing visual object.
        :param object_id: The unique ID of the object (body) to change.
        :param color: New RGBA color tuple (e.g., [0.5, 0.5, 0.5, 1] for gray).
        """
        with self._pybullet_api_lock:
            self._pybullet_api.changeVisualShape(
                objectUniqueId=object_id,
                linkIndex=-1, # -1 for the base visual shape
                rgbaColor=color,
                physicsClientId=self._physics_client
            )
            # self._pybullet_api.addUserDebugPoints(
            #     pointPositions=[position],
            #     pointColorsRGB=[1, 0, 0],
            #     pointSize=10,
            #     lifeTime=life_time,
            #     physicsClientId=self._physics_client
            # )
if __name__ == "__main__":
    # Create the simulated robot in GUI mode (window will open)
    sim = SimRobot(render_mode="human")
    sim.init_motors()
    for i in range(rl_config.STRESS_TEST_ITERS):
        cmd = []  # ← ajouter cette ligne ici !
        for j_idx, (min_l, max_l) in enumerate(rl_config.JOINT_LIMITS):
            span = max(abs(min_l), abs(max_l)) * 1.5
            angle = random.uniform(-span, span)
            cmd.append(angle)

        sim.move_abs_with_speed(cmd, speed=rl_config.MAX_SPEED)
    # Exemple : bouger le robot vers une position home


    # NEW: Define a sequence of positions to move the robot through
    positions = [
        [0, 0, 0, 0, 0, 0],
        [30, 0, 0, 0, 0, 0],
        [30, 30, 0, 0, 0, 0],
        [30, 30, 30, 0, 0, 0],
        [0, 0, 0, 0, 0, 0]
    ]

    # Move through the defined positions with a delay
    for pos in positions:
        sim.move_abs_with_speed(pos, speed=100)
        time.sleep(2)  # Wait 2 seconds between moves

    print("Simulation running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting simulation...")
        sim.shutdown()
