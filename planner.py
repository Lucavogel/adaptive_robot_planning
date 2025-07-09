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


import re

def extract_action_from_response(llm_response: str) -> str:
    # Sépare en lignes, strip, ignore lignes vides
    lines = [line.strip() for line in llm_response.strip().splitlines() if line.strip()]

    for i, line in enumerate(lines):
        # Enlève les * avant de checker
        clean_line = re.sub(r'\*+', '', line).strip().lower()

        # Cas Output: ...
        if clean_line.startswith("output:"):
            # Extrait tout après ':'
            parts = line.split(":", 1)
            if len(parts) > 1:
                action = parts[1].strip()
                if action:  # Si contenu sur la même ligne
                    return action
            # Sinon, cherche la prochaine ligne non vide
            for next_line in lines[i+1:]:
                if next_line.strip():
                    return next_line.strip()

        # Cas NEXT_EXERCISE: sur une ligne
        if line.startswith("NEXT_EXERCISE:"):
            return line.strip()

    return "No action found."
