cmake_minimum_required(VERSION 3.0.2)
project(adaptive_robot_planning)

## Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  moveit_commander
)

## Catkin specific configuration
catkin_package(
  CATKIN_DEPENDS rospy std_msgs moveit_commander
)

## Install Python scripts
catkin_install_python(PROGRAMS
  main.py
  camera_detection_node.py
  perception.py
  reasoning.py
  plan_and_execute.py
  planner.py
  speech_to_text.py
  text_to_speech.py
  config.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

## Install launch files
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

## Install other files
install(FILES
  knowledge_graph.json
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
