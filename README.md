

# Adaptive Robot Planning: Project Overview

This repository provides a complete framework for adaptive robot planning and control, with a focus on human-robot interaction and assistive robotics. The system is designed to enable a robotic arm to interpret, plan, and execute context-aware actions in dynamic environments, both in simulation and on real hardware.

## Objectives
- Develop a modular, extensible platform for adaptive robot behavior
- Integrate perception, reasoning, and action modules for closed-loop control
- Support research in neuro-symbolic AI, knowledge-graph reasoning, and LLM-based planning
- Enable reproducible experiments in assistive and collaborative robotics

## System Architecture
The project is organized into several core modules:
- **Perception:** Real-time object detection (YOLO), pose estimation (MediaPipe), and optional emotion recognition
- **Reasoning:** Knowledge-graph-based context integration, LLM-driven decision-making, and rule-based policy
- **Action Execution:** Symbolic-to-physical command mapping, trajectory planning (MoveIt 2), and ROS 2-based control of a UR robotic arm
- **Task Monitoring:** Real-time verification of user actions and feedback integration
- **Speech and Dialogue (optional):** Speech-to-text (Vosk), text-to-speech (gTTS), and dialogue management

## Technologies Used
- **ROS 2 Humble** for inter-module communication and robot control
- **Python** for high-level logic, perception, and reasoning
- **C++** for real-time arm control nodes
- **Gazebo** for simulation
- **MoveIt 2** for motion planning
- **OpenCV, YOLO, MediaPipe** for perception
- **Knowledge Graph (JSON)** for context and reasoning
- **LLM integration** (OpenRouter, HuggingFace, etc.) for adaptive planning

## Usage Scenarios
- Adaptive assistive robotics (e.g., stretching coach, collaborative tasks)
- Research in neuro-symbolic planning and explainable AI
- Benchmarking of perception-to-action pipelines
- Education and prototyping for advanced robotics

## Key Features
- Modular and extensible codebase
- Supports both simulation and real robot deployment
- Real-time, closed-loop adaptive planning
- Easy integration of new sensors, reasoning modules, or robot platforms
- Comprehensive documentation and example scripts



# System Launch: Full Adaptive Pipeline (with Ros2_projects workspace)

This project uses the `Ros2_projects` ROS 2 workspace as the central environment for simulation, robot control, and integration with the adaptive planning pipeline. All launch and build commands below assume you are working with this workspace.

To run the full adaptive system (perception, reasoning, action, and optional speech/dialogue), make sure you have:
- The knowledge graph file (`knowledge_graph.json`) present in the root folder
- All required models (YOLO, MediaPipe, Vosk, etc.) downloaded and placed in the correct directories
- The `Ros2_projects` workspace built and sourced (see below)


## 1. Build the ROS 2 workspace (Ros2_projects)

Open a terminal and go to the workspace folder:

```bash
cd /home/luca/Documents/GitHub/adaptive_robot_planning/Ros2_projects
source /opt/ros/humble/setup.bash
colcon build
```

After building, **source the environment**:

```bash
source install/setup.bash
```

## 2. Launch the robot simulation and MoveIt

In a first terminal:

```bash
cd /home/luca/Documents/GitHub/adaptive_robot_planning/Ros2_projects
source install/setup.bash
ros2 launch ur_simulation_gazebo ur_sim_moveit.launch.py
```

This opens Gazebo with the UR robot and MoveIt for motion planning.

## 3. Launch the arm control node

In a **second terminal**:

```bash
cd /home/luca/Documents/GitHub/adaptive_robot_planning/Ros2_projects
source install/setup.bash
ros2 run ik_move_cpp ik_move_cpp_node
```

This node listens for position commands on the `/target_point` topic.

## 4. Launch Perception and Reasoning (main.py)

In a **third terminal** (after launching the simulation and arm node):

```bash
cd /home/luca/Documents/GitHub/adaptive_robot_planning
source Ros2_projects/install/setup.bash
python3 main.py
```

This script orchestrates perception (object detection, pose, etc.), context retrieval, knowledge graph querying, LLM-based reasoning, and sends symbolic commands to the arm.

## 2. (Optional) Launch Speech-to-Text and Text-to-Speech

To enable speech recognition (STT) and speech synthesis (TTS), make sure your Vosk and gTTS models are installed and configured. The modules `speech_to_text.py` and `text_to_speech.py` are automatically called by `main.py` if enabled in the configuration.

## 3. (Optional) Camera Calibration and Spatial Referencing

For camera calibration and dynamic object localization, use the scripts in the `calibrage/` folder.

## 4. (Optional) Test Individual Modules

You can test individual modules:
- Perception: `python3 perception.py`
- Reasoning/knowledge graph: `python3 Query_knowledge_graph.py`
- Task monitoring: `python3 task_monitoring.py`
- Response verification: `python3 verification_loop.py`

---


# Command summary

```bash
# Terminal 1: Simulation + MoveIt
ros2 launch ur_simulation_gazebo ur_sim_moveit.launch.py

# Terminal 2: Arm control
ros2 run ik_move_cpp ik_move_cpp_node

# Terminal 3: Adaptive pipeline (perception, reasoning, etc.)
python3 main.py
```

---

## Common issues

- **"command not found" error**: Make sure you have sourced ROS 2 and the workspace (`source /opt/ros/humble/setup.bash` then `source install/setup.bash`)
- **The arm does not move**: Make sure the `ik_move_cpp_node` is running and that commands are being sent to `/target_point`
- **Need to rebuild**: After any change to the C++ code or workspace files, run `colcon build` again and then `source install/setup.bash`

---

For any questions, contact the project author or open an issue on the GitHub repository.
