# File: sim_sensor.py

import pybullet as p  # You can keep this import, though 'p' is now passed in
import numpy as np
import threading
import time


class SimNatNetDataHandler:
    def __init__(self, p_api, physics_client_id, robot_id, end_effector_link_id, pybullet_api_lock,
                 verbose=False):  # ADDED pybullet_api_lock
        self._p_api = p_api
        self._physics_client_id = physics_client_id
        self._robot_id = robot_id
        self._end_effector_link_id = end_effector_link_id
        self._pybullet_api_lock = pybullet_api_lock  # STORE the global PyBullet API lock
        self._verbose = verbose

        self.latest_relative_pos = np.zeros(3, dtype=np.float32)
        self.latest_relative_quat = np.array([0., 0., 0., 1.], dtype=np.float32)
        self._data_lock = threading.Lock()  # This lock is ONLY for guarding access to self.latest_relative_pos/quat

        # Initial call to update_data, will use the lock
        self.update_data()

    def update_data(self):
        # print(f"[SimNatNetDataHandler] Updating EEF data...")
        with self._pybullet_api_lock:  # ACQUIRE GLOBAL PYBULLET LOCK for getLinkState
            link_state = self._p_api.getLinkState(self._robot_id, self._end_effector_link_id,
                                                  physicsClientId=self._physics_client_id)
        # print(f"[SimNatNetDataHandler] Link state retrieved: {link_state}")

        # After getting data from PyBullet, then acquire _data_lock to update class attributes
        # with self._data_lock:
        eef_position = np.array(link_state[0])
        eef_orientation = np.array(link_state[1])
        self.latest_relative_pos = eef_position
        self.latest_relative_quat = eef_orientation

            # if self._verbose:
        # print(f"[SimNatNetDataHandler] EEF Pos (raw): {eef_position}, EEF Quat (raw): {eef_orientation}")


class SimNatNetClient:  # This class is from your original code, should be in sim_sensor.py too
    # ... (rest of SimNatNetClient code) ...
    # Placeholder for run_sim_sensor_client if it's imported elsewhere
    pass


def run_sim_sensor_client(natnet_client):  # This seems to be a dummy, ensure it exists if imported
    pass
