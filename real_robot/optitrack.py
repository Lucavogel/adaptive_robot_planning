import time
import numpy as np
import threading
from scipy.spatial.transform import Rotation as R
import logging



END_EFFECTOR_RB_ID = 12
TABLE_RB_ID = 11

natnet_logger = logging.getLogger('natnet')
natnet_logger.setLevel(logging.DEBUG) # Set level to DEBUG
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
natnet_logger.addHandler(ch)


class NatNetDataHandler:
    def __init__(self, verbose: bool = True):
        self.latest_rigid_bodies = []
        self.latest_markers = []
        self.latest_timing = None
        self.latest_relative_pos = None
        self.latest_relative_quat = None
        self.data_received_flag = False
        self.verbose = verbose
        self.is_connected = False  # New flag to indicate a successful connection to NatNet
        self._data_lock = threading.Lock()

    def dummy_callback(self, rigid_bodies: list[RigidBody], markers: list[LabelledMarker], timing: TimestampAndLatency):
        # print(f"[OptiTrack Thread] Callback triggered! Markers count: {len(markers)}, Timestamp: {timing.timestamp:.4f}s")
        # print(rigid_bodies)
        print(f"[OptiTrack DEBUG] markers: {markers}")

    def natnet_callback(self, rigid_bodies: list[RigidBody], markers: list[LabelledMarker], timing: TimestampAndLatency):
        """
        Callback function to handle incoming data from NatNet.
        Key changes of the optitrack watchdog should be inside the function.
        :param rigid_bodies:
        :param markers:
        :param timing:
        :return:
        """
        # Update raw data, protected by lock for thread-safety if other parts read it
        with self._data_lock:
            self.latest_rigid_bodies = rigid_bodies
            self.latest_markers = markers
            self.latest_timing = timing
            self.data_received_flag = True

        if self.verbose:
            print(f"[OptiTrack Thread] Callback triggered! Markers count: {markers}, Timestamp: {timing.timestamp:.4f}s") # For debugging callback
        # print(f'[OptiTrack Thread DEBUG] markers: {markers}')
        end_effector_rb = None
        table_rb = None
        # Find the specific rigid bodies by their IDs
        for rb in rigid_bodies:
            if rb.id_ == END_EFFECTOR_RB_ID:
                end_effector_rb = rb
            elif rb.id_ == TABLE_RB_ID:
                table_rb = rb
            # Break early if both are found
            if end_effector_rb and table_rb:
                break

        if end_effector_rb and table_rb:
            # Get positions (x, y, z)
            pos_ee_world = np.array(end_effector_rb.position)
            pos_table_world = np.array(table_rb.position)

            # Get orientations (qx, qy, qz, qw) - NatNet uses (x, y, z, w) order
            # scipy.spatial.transform.Rotation also expects (x, y, z, w)
            quat_ee_world = R.from_quat(end_effector_rb.orientation)
            quat_table_world = R.from_quat(table_rb.orientation)

            # 1. Calculate Relative Position
            # First, find the vector from table origin to end-effector origin in world coordinates.
            vec_ee_from_table_world = pos_ee_world - pos_table_world
            # print(vec_ee_from_table_world)
            # Then, rotate this vector into the table's local coordinate frame.
            # This gives the end-effector's position relative to the table's origin AND orientation.
            relative_pos = quat_table_world.inv().apply(vec_ee_from_table_world)

            # 2. Calculate Relative Orientation
            # Multiply the inverse of the table's orientation by the end-effector's orientation.
            # This gives the rotation from the table's frame to the end-effector's frame.
            relative_rot = quat_table_world.inv() * quat_ee_world
            relative_quat = relative_rot.as_quat()  # Get the quaternion (x, y, z, w)
            relative_euler = relative_rot.as_euler('xyz',
                                                   degrees=True)  # Get Euler angles (roll, pitch, yaw) in degrees

            if self.verbose:
                print(f"[OptiTrack Thread] \n--- Relative Pose (Timestamp: {timing.timestamp:.4f}s) ---")
                print(f"[OptiTrack Thread] End-effector ({END_EFFECTOR_RB_ID}) relative to Table ({TABLE_RB_ID}):")
                print(f"[OptiTrack Thread] Position (x,y,z): {relative_pos[0]:.4f}, {relative_pos[1]:.4f}, {relative_pos[2]:.4f} meters")
                print(
                    f"[OptiTrack Thread] Orientation (Quat x,y,z,w): {relative_quat[0]:.4f}, {relative_quat[1]:.4f}, {relative_quat[2]:.4f}, {relative_quat[3]:.4f}")
                print(
                    f"[OptiTrack Thread] Orientation (Euler deg Roll,Pitch,Yaw): {relative_euler[0]:.4f}, {relative_euler[1]:.4f}, {relative_euler[2]:.4f} degrees")

            # --- Your robot control logic goes here ---
            # Example: Assuming your robot library expects a position and a quaternion
            # robot.set_pose_relative_to_table(relative_pos, relative_quat)
            with self._data_lock:
                self.latest_relative_pos = relative_pos
                self.latest_relative_quat = relative_quat
            # print(f'pos: {relative_pos}')

        else:
            if not end_effector_rb:
                print(f"[OptiTrack Thread] Warning: End-effector RB with ID {END_EFFECTOR_RB_ID} not found in this frame.")
            if not table_rb:
                print(f"[OptiTrack Thread] Warning: Table RB with ID {TABLE_RB_ID} not found in this frame.")
            print("Cannot calculate relative pose without both rigid bodies.")


# Function to run the NatNet client in a separate thread
def run_natnet_client_in_thread(data_handler: NatNetDataHandler, ip_address: str):
    """
    Connects to the NatNet server and starts the blocking `spin()` loop
    in a dedicated thread.
    """
    print(f'[OptiTrack Thread] Attempting to connect to {ip_address}...')
    try:
        client = natnet.Client.connect(ip_address, logger=natnet_logger, timeout=5)
        print('[OptiTrack Thread] Client connected successfully.')
        data_handler.is_connected = True
        client.set_callback(data_handler.natnet_callback)
        print('[OptiTrack Thread] Callback set. Starting data acquisition loop (blocking).')
        client.spin() # This call blocks the thread until interrupted
    except natnet.DiscoveryError as e:
        print(f"[OptiTrack Thread] Error: Failed to connect to {ip_address}: {e}")
        print("[OptiTrack Thread] Ensure Motive/OptiTrack software is running, NatNet streaming is enabled, and IP/firewall settings are correct.")
    except Exception as e:
        print(f"\n[OptiTrack Thread] An unexpected error occurred: {e}")
    finally:
        print("[OptiTrack Thread] Client thread exiting.")
        data_handler.is_connected = False # Indicate disconnection