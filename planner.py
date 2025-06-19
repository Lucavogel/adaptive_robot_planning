def extract_action_from_response(llm_response: str) -> str:
    for line in llm_response.strip().splitlines():
        if line.lower().startswith("output:"):
            return line.split(":", 1)[1].strip()
    return "No action found."
