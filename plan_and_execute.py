#!/usr/bin/env python3
import rospy
import re
from moveit_commander import MoveGroupCommander, RobotCommander, roscpp_initialize

# Initialisation MoveIt!
roscpp_initialize([])
rospy.init_node('plan_executor_node', anonymous=True)
group = MoveGroupCommander("manipulator")
robot = RobotCommander()

# Coordonnées associées aux objets
OBJECT_POSITIONS = {
    "GLASS":  [0.4, 0.1, 0.3],
    "BANANA": [0.5, -0.2, 0.25],
    "TOWEL":  [0.3, 0.3, 0.2],
}

def execute_llm_decision(llm_response):
    output_match = re.search(r"Output:\s*\"?(.+?)\"?$", llm_response, re.DOTALL)
    if not output_match:
        print("❌ Aucun Output reconnu.")
        return False

    llm_output = output_match.group(1).strip()
    print("💬 LLM Output:", llm_output)

    point_match = re.search(r"\bPOINT_([A-Z]+)\b", llm_output)
    if not point_match:
        print("🤖 Aucun objet à pointer détecté.")
        return False

    object_name = point_match.group(1).upper()
    if object_name not in OBJECT_POSITIONS:
        print(f"⚠️ Objet inconnu : {object_name}")
        return False

    position = OBJECT_POSITIONS[object_name]
    rospy.loginfo(f"🤖 Mouvement vers {object_name} à {position}")
    group.set_position_target(position)
    success = group.go(wait=True)
    group.stop()
    group.clear_pose_targets()

    if success:
        rospy.loginfo("✅ Mouvement réussi.")
        return True
    else:
        rospy.logwarn("❌ Mouvement échoué.")
        return False
