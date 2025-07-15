# File: sim_robot.py

import os
import pybullet as p  # Keep this import as p
import pybullet_data
import time
import threading
import numpy as np
import subprocess
import tempfile
import atexit # Import atexit for cleanup


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

        self._target_position_rad = 0.0 # Reverted to original name (was _target_position_reg)

    def genericRead_Blocking_int(self, cmd):
        if cmd == "QD":
            with self._pybullet_api_lock:
                try:
                    joint_state = self._p_api.getJointState(self._robot_id, self._joint_id, physicsClientId=self._physics_client_id)
                    return int(np.degrees(joint_state[0]) * 100)
                except p.error as e:
                    # Removed detailed error logging as per API alignment, but kept basic notice.
                    return None
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
        with self._pybullet_api_lock:
            target_pos_rad = np.radians(pos_centi_deg / 100.0)
            # Removed logging for API alignment
            self._target_position_rad = target_pos_rad # Reverted to original name
            self._p_api.setJointMotorControl2(
                bodyUniqueId=self._robot_id,
                jointIndex=self._joint_id,
                controlMode=self._p_api.POSITION_CONTROL,
                targetPosition=target_pos_rad,
                maxVelocity=10,
                physicsClientId=self._physics_client_id
            )

    def move_abs_with_speed(self, pos_centi_deg, speed):
        with self._pybullet_api_lock:
            target_pos_rad = np.radians(pos_centi_deg / 100.0)
            # Removed logging for API alignment
            self._target_position_rad = target_pos_rad # Reverted to original name
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
    # Change __init__ signature to match Robot class
    def __init__(self, portname=None):
        self._bus = None # Now acts as a flag for PyBullet connection status
        self._bus_lock = threading.Lock()
        self._motor_ids = [0, 1, 2, 3, 4, 5]
        self._portname = portname # Parameter for API alignment, not directly used in sim
        self._motors = []
        atexit.register(self.close_bus) # Register cleanup

        # PyBullet specific attributes, initialized to None until init_bus()
        self._pybullet_api = None
        self._physics_client = None
        self._robot_id = None
        self._pybullet_api_lock = threading.Lock() # Global PyBullet API lock
        self._controlled_joint_indices = []
        self._end_effector_link_id = -1

        self.home_position = [0, 0, 0, 0, 0, 0]
        self._in_emergency_state = False
        self._emergency_thread = None
        self._emergency_time = 0.5 # Default emergency time

        # NEW: Store the last read joint angles (in degrees)
        self._current_joint_angles_deg = [0.0] * len(self._motor_ids)

    def init_bus(self):
        # This function now handles PyBullet client connection and robot loading
        print("[SimRobot] Initializing PyBullet client and loading robot...")
        try:
            # Connect to PyBullet only if not already connected
            if self._physics_client is None:
                self._pybullet_api = p
                with self._pybullet_api_lock:
                    self._physics_client = self._pybullet_api.connect(self._pybullet_api.GUI) # Default to GUI for simplicity

                self._pybullet_api.setAdditionalSearchPath(pybullet_data.getDataPath())
                self._pybullet_api.setGravity(0, 0, -9.81)
                self._bus = True # Set bus to True after successful connection

            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root_dir = os.path.abspath(os.path.join(current_script_dir))
            URDF_SOURCE_FILE = "ur5.urdf" # Or "ur5_robot.urdf.xacro" if you changed it back
            robot_description_base_path = os.path.join(project_root_dir, "robot_models", "ur_description", "urdf")
            SOURCE_FILE_PATH = os.path.join(robot_description_base_path, URDF_SOURCE_FILE)

            with self._pybullet_api_lock: # ACQUIRE LOCK for setAdditionalSearchPath
                self._pybullet_api.setAdditionalSearchPath(robot_description_base_path)

            urdf_load_path = SOURCE_FILE_PATH
            temp_urdf_path = None
            if URDF_SOURCE_FILE.endswith(".xacro"):
                try:
                    temp_urdf_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.urdf')
                    temp_urdf_path = temp_urdf_file.name
                    temp_urdf_file.close()
                    cmd = ["xacro", "--inorder", SOURCE_FILE_PATH]
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    with open(temp_urdf_path, 'w') as f:
                        f.write(result.stdout)
                    urdf_load_path = temp_urdf_path
                    print(f"[SimRobot] XACRO processed. Generated temporary URDF at: {temp_urdf_path}")
                except Exception as e:
                    print(f"[SimRobot] Error processing XACRO: {e}")
                    raise

            with self._pybullet_api_lock: # ACQUIRE LOCK for loadURDF
                URDF_SPAWN_HEIGHT = 0.0  # Example value, adjust as needed

                self._robot_id = self._pybullet_api.loadURDF(
                    urdf_load_path,
                    [0, 0, URDF_SPAWN_HEIGHT],  # <- MODIFIED: Increased Z-coordinate
                    useFixedBase=True,
                    physicsClientId=self._physics_client
                )
            if temp_urdf_path and os.path.exists(temp_urdf_path):
                os.remove(temp_urdf_path)
                print(f"[SimRobot] Cleaned up temporary URDF: {temp_urdf_path}")

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
            # Removed render_mode specific time.sleep for API alignment.
            return True
        except Exception as e:
            print(f"[SimRobot] Error during robot loading/initialization: {e}")
            self._bus = False
            return False

    def close_bus(self):
        if self._physics_client is not None:
            with self._pybullet_api_lock:
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
        self._emergency_recovery_task()

    def _emergency_recovery_task(self):
        print("\n" + "=" * 40)
        print("! ! ! SIM ROBOT ENTERING EMERGENCY RECOVERY ! ! !")
        print("[Emergency] Holding all joints...")
        self.hold()
        time.sleep(self._emergency_time)

        print(f"[Emergency] Moving to safe home position: {self.home_position}")
        self._move_and_wait_admin(self.home_position, sim_steps_per_check=50)

        print("[Emergency] _move_and_wait in recovery finished (may have timed out).")

        self._in_emergency_state = False
        print("[Emergency] Home position reached. Resuming normal operation.")
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

    # Removed draw_debug_sphere and change_sphere_color for API alignment.
    # Removed get_info for API alignment.

    # BEGIN NEW GETTER METHODS FOR MAIN_SIM.PY
    def get_pybullet_api(self):
        return self._pybullet_api

    def get_physics_client_id(self):
        return self._physics_client

    def get_robot_id(self):
        return self._robot_id

    def get_end_effector_link_id(self):
        return self._end_effector_link_id

    def get_pybullet_api_lock(self):
        return self._pybullet_api_lock
    # END NEW GETTER METHODS
