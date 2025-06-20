def extract_action_from_response(llm_response: str) -> str:
    lines = [line.strip() for line in llm_response.strip().splitlines() if line.strip()]
    for i, line in enumerate(lines):
        # Cas Output: NEXT_EXERCISE: ...
        if line.lower().startswith("output:"):
            action = line.split(":", 1)[1].strip()
            if action:  # Si la ligne Output: contient déjà l'action
                return action
            # Sinon, prend la ligne suivante non vide
            for next_line in lines[i+1:]:
                if next_line:
                    return next_line
        # Cas NEXT_EXERCISE: seul
        if line.startswith("NEXT_EXERCISE:"):
            return line
    return "No action found."
