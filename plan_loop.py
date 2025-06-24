#!/usr/bin/env python3
import rospy
import time
from moveit_commander import MoveGroupCommander, RobotCommander, roscpp_initialize
from reasoning import reason_with_context
import re
from geometry_msgs.msg import Pose

roscpp_initialize([])
rospy.init_node('plan_loop_node', anonymous=True)

robot = RobotCommander()
group = MoveGroupCommander("manipulator")

# 📍 Position des objets
OBJECT_POSITIONS = {
    "GLASS":  [0.6, -0.4, 0.5],
    "BANANA": [0.6, 0, 0.5],
    "TOWEL":  [0.6, 0.4, 0.5],
}

# 💾 Capture position initiale (pose actuelle)
initial_pose = group.get_current_pose().pose
rospy.loginfo(f"🔁 Position initiale capturée: {initial_pose}")

# 🔁 Simulation de contextes/dialogues
test_cases = [
    ({"thirsty": True}, ["User: It's really hot today."]),
    ({"tired": True}, ["User: I'm feeling a bit tired."]),
    ({"sweaty": True}, ["User: I'm sweating a lot."]),
    ({"thirsty": True, "tired": True}, ["User: This stretch is hard...", "User: Do I have to do it now?"]),
]

last_motion_time = time.time()
last_object = None

for context, dialogue in test_cases:
    rospy.loginfo(f"\n🔁 Étape — contexte: {context}, dialogue: {dialogue}")

    step = {"id": "X", "action": "move_to", "target": [0.4, 0.0, 0.4]}
    decision = reason_with_context(step, context, next_exercise=None, dialogue_history=dialogue)
    print("🧠 LLM Decision:\n", decision)

    output_match = re.search(r"Output:\s*\"?(.*?)\"?$", decision, re.DOTALL)
    if output_match:
        llm_output = output_match.group(1).strip()
        print("💬 LLM Output:", llm_output)

        point_match = re.search(r"\bPOINT_([A-Z]+)\b", llm_output)
        if point_match:
            object_name = point_match.group(1)
            pos = OBJECT_POSITIONS.get(object_name)
            if pos:
                if object_name != last_object:
                    rospy.loginfo(f"🤖 Mouvement vers {object_name} à {pos}")
                    group.set_position_target(pos)
                    success = group.go(wait=True)
                    group.stop()
                    group.clear_pose_targets()
                    if success:
                        rospy.loginfo("✅ Mouvement réussi.")
                        last_motion_time = time.time()
                        last_object = object_name
                    else:
                        rospy.logerr("❌ Échec du mouvement.")
            else:
                rospy.logwarn(f"⚠️ Objet inconnu: {object_name}")
        else:
            print("🤖 Aucun mouvement nécessaire.")

    else:
        print("❌ LLM Output non reconnu.")

  