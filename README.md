# Adaptive Robot Planning - Exercise Coaching System

An intelligent ROS-based robot coaching system that combines real-time object detection, natural language processing, and adaptive planning to guide users through personalized exercise routines.

## Features

- Real-time Object Detection: YOLO-based computer vision for detecting objects like cups, bottles, laptops
- Adaptive Exercise Coaching: AI-powered exercise guidance that adapts to user state and feedback
- Voice Interaction: Speech-to-text and text-to-speech for natural conversation
- Robot Arm Control: MoveIt! integration for UR5 robot arm pointing gestures
- Knowledge-based Reasoning: Uses knowledge graphs and LLM reasoning for intelligent responses

## Prerequisites

### System Requirements
- OS: Ubuntu 20.04 LTS
- ROS: ROS Noetic



### Dependencies
```bash
# ROS packages
sudo apt-get install ros-noetic-moveit ros-noetic-usb-cam ros-noetic-cv-bridge

# Python packages
pip install ultralytics opencv-python gtts pygame sounddevice vosk openai
```

## Installation

1. Clone the repository:
```bash
cd ~/catkin_ws/src
git clone <your-repo-url> adaptive_robot_planning
```

2. Install dependencies:
```bash
cd adaptive_robot_planning
pip install -r requirements.txt
```

3. Build workspace:
```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

## Usage

Run the complete system with these commands in separate terminals:

**Terminal 1 - ROS Core:**
```bash
roscore
```

**Terminal 2 - Camera:**
```bash
roslaunch adaptive_robot_planning webcam.launch
```

**Terminal 3 - Robot Simulation:**
```bash
roslaunch ur5_moveit_config demo.launch
```

**Terminal 4 - Object Detection:**
```bash
python3 camera_detection_node.py
```

**Terminal 5 - Main Program:**
```bash
python3 main.py
```

## Project Structure

```
adaptive_robot_planning/
├── main.py                    # Main coaching logic
├── camera_detection_node.py   # Real-time object detection
├── perception.py              # Perception interface
├── reasoning.py               # LLM-based reasoning
├── plan_and_execute.py        # Robot arm control
├── speech_to_text.py          # Voice input processing
├── text_to_speech.py          # Voice output synthesis
├── config.py                  # API configuration
├── knowledge_graph.json       # Domain knowledge base
└── launch/webcam.launch       # Camera launch file
```

## Configuration

### API Keys
Update `config.py`:
```python
API_KEY = "your-openrouter-api-key"
MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1:free"
```

### Object Detection
Modify `OBJECT_POSITIONS` in `plan_and_execute.py`:
```python
OBJECT_POSITIONS = {
    "CUP": [0.4, 0.1, 0.3],
    "BOTTLE": [0.4, 0.1, 0.3],
    "LAPTOP": [0.4, 0.0, 0.3],
}
```

### Camera Issues
```bash
# Check cameras
ls /dev/video*

# Test camera
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Works:', cap.isOpened())"
```