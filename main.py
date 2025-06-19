from perception import get_environment_context
from reasoning import reason_with_context
from planner import extract_action_from_response

def main():
    context = get_environment_context()
    print("🧠 Perceived context:\n", context)

    llm_response = reason_with_context(context)
    print("\n🤖 Full LLM reasoning:\n", llm_response)

    action = extract_action_from_response(llm_response)
    print("\n✅ Planned Action:", action)

if __name__ == "__main__":
    main()
