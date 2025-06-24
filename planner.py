import re


def clean_llm_response(text: str) -> str:
    # Retire les **, guillemets, et espaces superflus
    text = re.sub(r'[\*\"]+', '', text)
    text = text.strip()
    # Retire POINT_XXX au début
    text = re.sub(r'^POINT_[A-Z_]+\s*', '', text)
    # Retire NEXT_EXERCISE: ... au début
    text = re.sub(r'^NEXT_EXERCISE:\s*', '', text, flags=re.IGNORECASE)
    # Retire STOP_ROUTINE au début
    text = re.sub(r'^STOP_ROUTINE\s*', '', text, flags=re.IGNORECASE)
    return text.strip()


# Exemple d'utilisation :
# response = '✅ Robot Action: POINT_BANANA It seems like you\'re also feeling a bit hungry! Would you like to **eat the banana** here to refresh your energy before we move on to **Touch your toes**?'
# print(clean_llm_response(response))


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
