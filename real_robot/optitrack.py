import time
import numpy as np
import threading
from scipy.spatial.transform import Rotation as R
import logging

from NatNetClient import NatNetClient

END_EFFECTOR_RB_ID = 12
TABLE_RB_ID = 11

natnet_logger = logging.getLogger('natnet')
natnet_logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
natnet_logger.addHandler(ch)


class NatNetDataHandler:
    def __init__(self, verbose: bool = True):
        self.rigid_bodies = {}  # id -> (position, orientation)
        self.verbose = verbose
        self.latest_relative_pos = None
        self.latest_relative_quat = None
        self._data_lock = threading.Lock()

    def rigid_body_callback(self, id, position, orientation):
        with self._data_lock:
            self.rigid_bodies[id] = (np.array(position), np.array(orientation))

        if self.verbose:
            print(f"[OptiTrack] Received RB ID {id} → pos: {position}, orient: {orientation}")

        with self._data_lock:
            if END_EFFECTOR_RB_ID in self.rigid_bodies and TABLE_RB_ID in self.rigid_bodies:
                pos_ee, quat_ee = self.rigid_bodies[END_EFFECTOR_RB_ID]
                pos_table, quat_table = self.rigid_bodies[TABLE_RB_ID]

                quat_ee_world = R.from_quat(quat_ee)
                quat_table_world = R.from_quat(quat_table)

                vec_ee_from_table = pos_ee - pos_table
                relative_pos = quat_table_world.inv().apply(vec_ee_from_table)

                relative_rot = quat_table_world.inv() * quat_ee_world
                relative_quat = relative_rot.as_quat()
                relative_euler = relative_rot.as_euler('xyz', degrees=True)

                if self.verbose:
                    print(f"\n[OptiTrack] --- Relative Pose ---")
                    print(f"[OptiTrack] Relative Position: {relative_pos}")
                    print(f"[OptiTrack] Relative Orientation (quat): {relative_quat}")
                    print(f"[OptiTrack] Relative Orientation (euler deg): {relative_euler}")

                self.latest_relative_pos = relative_pos
                self.latest_relative_quat = relative_quat


def run_natnet_client_in_thread(data_handler: NatNetDataHandler, server_ip: str = "127.0.0.1"):
    def run():
        client = NatNetClient(serverIPAddress=server_ip)
        client.rigidBodyListener = data_handler.rigid_body_callback
        print(f"[OptiTrack] Connecting to server at {server_ip}...")
        client.run()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
