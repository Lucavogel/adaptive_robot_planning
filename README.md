# Adaptive Robot Planning - UR Robotic Arm Control (ROS 2 Humble)

This guide explains how to launch the robotic arm part of the project, **even if you are not familiar with ROS 2**.

---

## Prerequisites

- **ROS 2 Humble** installed ([official guide](https://docs.ros.org/en/humble/Installation.html))
- Ubuntu 22.04 recommended
- This repository cloned on your machine
- Python dependencies installed:
  ```bash
  ```
- The ROS 2 workspace (`UR_WS`) built at least once (see below)

---

## 1. Build the ROS 2 workspace

Open a terminal and go to the workspace folder:

```bash
cd /home/luca/Documents/GitHub/adaptive_robot_planning/UR_WS
source /opt/ros/humble/setup.bash
colcon build
```

After building, **source the environment**:

```bash
source install/setup.bash
```

---

## 2. Launch the robot simulation and MoveIt

In a first terminal:

```bash
cd /home/luca/Documents/GitHub/adaptive_robot_planning/UR_WS
source install/setup.bash
ros2 launch ur_simulation_gazebo ur_sim_moveit.launch.py
```

This opens Gazebo with the UR robot and MoveIt for motion planning.

---

## 3. Launch the arm control node

In a **second terminal**:

```bash
cd /home/luca/Documents/GitHub/adaptive_robot_planning/UR_WS
source install/setup.bash
ros2 run ik_move_cpp ik_move_cpp_node
```

This node listens for position commands on the `/target_point` topic.

---

## 4. Test sending commands to the arm

In a **third terminal**:

```bash
cd /home/luca/Documents/GitHub/adaptive_robot_planning
source ../UR_WS/install/setup.bash
python3 test_robot_positions.py
```

You can then choose to send:
- `POINT_BANANA`
- `POINT_GLASS`
- `POINT_TOWEL`

The arm will move to the corresponding position in the simulation.

---

## 5. Using the main system (main.py)

If you run the main system (`main.py`), make sure:
- Steps 2 and 3 are already running (simulation + arm node)
- The Python script will automatically publish commands to `/target_point` via the `LLMCommander` class

---

## Command summary

```bash
# Terminal 1: Simulation + MoveIt
ros2 launch ur_simulation_gazebo ur_sim_moveit.launch.py

# Terminal 2: Arm control
ros2 run ik_move_cpp ik_move_cpp_node

# Terminal 3 (optional): Test sending commands
python3 test_robot_positions.py
```

---

## Common issues

- **"command not found" error**: Make sure you have sourced ROS 2 and the workspace (`source /opt/ros/humble/setup.bash` then `source install/setup.bash`)
- **The arm does not move**: Make sure the `ik_move_cpp_node` is running and that commands are being sent to `/target_point`
- **Need to rebuild**: After any change to the C++ code or workspace files, run `colcon build` again and then `source install/setup.bash`

---

For any questions, contact the project author or open an issue on the GitHub repository.
