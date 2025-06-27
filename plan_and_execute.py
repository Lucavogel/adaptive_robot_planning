#!/usr/bin/env python3
import rospy
import re
from moveit_commander import MoveGroupCommander, RobotCommander, roscpp_initialize

roscpp_initialize([])
group = MoveGroupCommander("manipulator")
robot = RobotCommander()

OBJECT_POSITIONS = {
    "GLASS":  [0.4, 0.1, 0.3],
    "CUP":    [0.4, 0.1, 0.3],
    "BOTTLE": [0.4, 0.1, 0.3],
    "BANANA": [0.5, -0.2, 0.25],
    "TOWEL":  [0.3, 0.3, 0.2],
    "PERSON": [0.6, 0.0, 0.4],
    "CELL PHONE": [0.3, 0.2, 0.25],
    "BOOK": [0.4, -0.1, 0.25],
    "LAPTOP": [0.4, 0.0, 0.3],
    "REMOTE": [0.3, 0.1, 0.25],
}

def execute_llm_decision(llm_response: str) -> bool:
    
    match = re.search(r"POINT_([A-Z]+)", llm_response)
    if not match:
        print("no object-point command in LLM response")
        return False

    obj = match.group(1)
    if obj not in OBJECT_POSITIONS:
        rospy.logwarn(f"object '{obj}' not in OBJECT_POSITIONS mapping")
        return False

    target = OBJECT_POSITIONS[obj]
    rospy.loginfo(f"pointing to {obj} at {target}")

    group.set_position_target(target)
    success = group.go(wait=True)
    group.stop()
    group.clear_pose_targets()

    if success:
        rospy.loginfo("movement successful.")
    else:
        rospy.logwarn("movement failed.")
    return success
