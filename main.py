#!/usr/bin/env python3

import rospy
import re
from reasoning import reason_with_context
from planner import extract_action_from_response
from perception import get_environment_context, get_latest_objects
from speech_to_text import listen_until_silent
from text_to_speech import speak
from plan_and_execute import execute_llm_decision

memory = []
exercise_sequence = [
    "Stretch your arms",
    "Touch your toes",
    "Rotate your neck"
]

def main():
    rospy.init_node("adaptive_coach", anonymous=True)
    dialogue_history = []

    
    intro_response = reason_with_context(
        context_description="",
        current_exercise="",
        next_exercise=exercise_sequence[0]
    )
    print("intro :", intro_response)
    action = extract_action_from_response(intro_response)
    speak(action)
    memory.append(action)
    dialogue_history.append(f"Robot: {action}")

    # exercices loop
    for i, exercise in enumerate(exercise_sequence):
        print(f"\n exercise {i+1}: {exercise}")
        next_exercise = exercise_sequence[i + 1] if i + 1 < len(exercise_sequence) else ""

        # get environment context
        perception_context = get_environment_context()
        print(perception_context)

        
        current_objects = get_latest_objects()
        if any(obj.lower() in ("cup", "bottle") for obj in current_objects):
            fake_resp = 'Output: POINT_CUP "Here is a cup of water."'
            execute_llm_decision(fake_resp)
            speak("Here is a cup of water. Please take a sip!")
            continue

        # our input
        human_input = input("Human: ")
        if human_input:
            print(f"Human: {human_input}")
            dialogue_history.append(f"Human: {human_input}")

        # call LLM 
        llm_response = reason_with_context(
            context_description=perception_context + "\n" + "\n".join(dialogue_history),
            current_exercise=exercise,
            next_exercise=next_exercise,
            dialogue_history=dialogue_history
        )
        print("\n model reasoning:\n", llm_response)

        execute_llm_decision(llm_response)

        action = extract_action_from_response(llm_response)
        print(" ###Robot Action####", action)
        spoken = re.sub(r"POINT_[A-Z]+", "", action).strip()
        speak(spoken)

        memory.append(action)
        dialogue_history.append(f"######robot: {action}#####")

        # NEXT_EXERCISE
        if action.startswith("NEXT_EXERCISE:"):
            continue

    print("\n end of routine")
    print("\n############ full Conversation Log #############")
    for line in dialogue_history:
        print(line)

    # LLM conclusion
    outro = reason_with_context(
        context_description="\n".join(dialogue_history),
        current_exercise="",
        next_exercise="",
        dialogue_history=dialogue_history
    )
    print("robot output:", outro)
    speak(outro)
    dialogue_history.append(f"robot: {outro}")

if __name__ == "__main__":
    main()
