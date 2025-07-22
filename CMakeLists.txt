cmake_minimum_required(VERSION 3.0.2)
project(adaptive_robot_planning)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  geometry_msgs
  cv_bridge
  tf
)

catkin_package()

# Installation des scripts Python (sans dossier scripts/)
catkin_install_python(PROGRAMS
  main.py
  aruco_detector.py
  camera_detection_node.py
  aruco_arm_controller.py
  perception.py
  reasoning.py
  text_to_speech.py
  speech_to_text.py
  config.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# Installation des fichiers de données
install(FILES
  knowledge_graph.json
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

# Installation des launch files
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
