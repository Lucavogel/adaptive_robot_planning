# rl_config.py - Configuration Constants for RL Robot Environment

# --- Robot Configuration ---
PORT = '/dev/ttyACM0'  # Serial port for your robot
JOINT_LIMITS = [
    (-180, 180),  # Joint 0 (Base Rotation)
    (-85, 85),   # Joint 1 (Shoulder)
    (-160, 160), # Joint 2 (Elbow)
    (-180, 180), # Joint 3 (Wrist Yaw)
    (-180, 180), # Joint 4 (Wrist Pitch)
    (-180, 180), # Joint 5 (Gripper Rotation)
]
MAX_SPEED = 1000 # Max speed for robot movements

# --- OptiTrack Configuration ---
NATNET_SERVER_IP = '192.168.1.132'  # IP address of the machine running Motive/OptiTrack
NATNET_CONNECT_TIMEOUT = 5  # seconds for NatNet connection timeout

# --- Workspace and Target Configuration (in meters) ---
# Estimated robot workspace for observation space normalization
WORKSPACE_MIN_X = -0.3
WORKSPACE_MAX_X = 0.3
WORKSPACE_MIN_Y = 0.3
WORKSPACE_MAX_Y = 0.8
WORKSPACE_MIN_Z = -0.3
WORKSPACE_MAX_Z = 0.3

# Min/Max values for target positions (within the robot's reachable workspace)
TARGET_MIN_X = -0.25
TARGET_MAX_X = 0.25
TARGET_MIN_Y = 0.35
TARGET_MAX_Y = 0.75
TARGET_MIN_Z = -0.25
TARGET_MAX_Z = 0.25

# --- Environment Parameters ---
ACTION_RANGE_DEG = 3.0  # Max degrees change per joint per training step
GOAL_TOLERANCE_M = 0.05  # 5 cm tolerance for reaching the goal
MAX_STEPS_PER_EPISODE = 300  # Max steps before episode times out
REWARD_SCALING_FACTOR = 10.0  # Scale reward to make it more impactful to the agent
ACTION_EXECUTION_TIME_SEC = 0.05 # Time to wait after sending motor commands for robot to move and OptiTrack to update.

# --- Training Configuration ---
LOG_DIR = "./rl_logs_sac/" # Directory for TensorBoard logs and saved models
MODEL_SAVE_FREQ = 25000 # Save model checkpoint every X timesteps
TOTAL_TIMESTEPS = 100000 # Total timesteps to train the agent in the environment
LEARNING_RATE = 0.0003 # Learning rate for the SAC algorithm
BATCH_SIZE = 256 # Batch size for gradient updates
GAMMA = 0.99 # Discount factor
TAU = 0.005 # Soft update coefficient for the target networks
TRAIN_FREQ = (1, "step") # Update policy after every environment step
GRADIENT_STEPS = 1 # Number of gradient steps after each rollout

# --- Testing Configuration ---
NUM_TEST_EPISODES = 5 # Number of episodes to test the agent

# --- Main Script/Stress Test Configuration ---
WATCHDOG_INTERVAL = 0.0 # Interval for safety watchdog checks
MARKER_RADII = {
    # Example:
    1: 0.025,  # Marker with ID 1, radius 2cm
    2: 0.025,  # Marker with ID 2, radius 2cm
    3: 0.025,  # Marker with ID 3, radius 2cm
    4: 0.025,  # Marker with ID 4, radius 2cm
    5: 0.025,  # Marker with ID 5, radius 2cm
    6: 0.025,  # Marker with ID 6, radius 2cm
    # Add more markers as needed. Markers NOT in this dict will be ignored for sphere checks.
}
STRESS_TEST_ITERS = 2000 # Max number of random commands for stress test
STRESS_TEST_INTERVAL = 2 # Seconds between commands (i.e. 2 Hz)
