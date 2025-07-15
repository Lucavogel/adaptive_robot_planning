import robot
import time
import numpy as np
from scipy.spatial.transform import Rotation as R

import natnet
import logging # Import logging module
from natnet.protocol.MocapFrameMessage import LabelledMarker, RigidBody
from natnet.comms import TimestampAndLatency # Correct import for the timing object
from optitrack import NatNetDataHandler


natnet_logger = logging.getLogger('natnet')
natnet_logger.setLevel(logging.DEBUG) # Set level to DEBUG
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
natnet_logger.addHandler(ch)

try:
    client = natnet.Client.connect('192.168.1.132', logger=natnet_logger, timeout=5) # Increased timeout for connection
    print('[NatNet] Client connected')
except natnet.DiscoveryError as e:
    print(f"[NatNet] Error: Failed to connect: {e}")
    print("Please ensure Motive/OptiTrack software is running, NatNet streaming is enabled, and IP/firewall settings are correct.")
    exit() # Exit if connection fails

data_handler = NatNetDataHandler(verbose=False)
client.set_callback(data_handler.natnet_callback)
print('[NatNet] Callback set')
print('[NatNet] Starting continuous data acquisition loop...')
try:
    client.spin()

except KeyboardInterrupt:
    print("\n[NatNet] KeyboardInterrupt detected. Stopping client.")
except Exception as e:
    print(f"\n[NatNet] Error: {e}")
finally:
    print("[NatNet] Exiting.")