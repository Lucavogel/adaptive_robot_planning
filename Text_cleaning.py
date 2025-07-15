import re


def clean_llm_response(text: str) -> str:
    text = re.sub(r'[\*"]+', '', text)  # Supprime guillemets et **
    text = text.strip()
    text = re.sub(r'^POINT_[A-Z_]+\s*', '', text)
    text = re.sub(r'^NEXT_EXERCISE:\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^STOP_ROUTINE\s*', '', text, flags=re.IGNORECASE)
    return text.strip()


# Exemple d'utilisation :
# response = '✅ Robot Action: POINT_BANANA It seems like you\'re also feeling a bit hungry! Would you like to **eat the banana** here to refresh your energy before we move on to **Touch your toes**?'
# print(clean_llm_response(response))


def extract_action_from_response(llm_response: str) -> str:
    # Enlève tous les ** et espaces superflus AVANT le parsing
    cleaned = "\n".join(line.replace("**", "").strip() for line in llm_response.strip().splitlines())
    lines = [line for line in cleaned.splitlines()]
    output_found = False

    for i, line in enumerate(lines):
        # Cas Output: (inchangé)
        if re.match(r"output\s*[:：]?\s*$", line, flags=re.IGNORECASE):
            output_found = True
            for next_line in lines[i+1:]:
                next_line = next_line.strip()
                if next_line and not next_line.lower().startswith("✅ robot action"):
                    return next_line
        else:
            # Cas Output: sur la même ligne (inchangé)
            match = re.match(r"output\s*[:：]?\s*(.+)", line, flags=re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    return content
            # Détecte "✅ Robot Action:" même avec des étoiles ou espaces
            match_action = re.match(r"✅\s*robot action\s*[:：]?\s*(.*)", line, flags=re.IGNORECASE)
            if match_action:
                content = match_action.group(1).strip()
                if content:
                    return content

    return "No output found."



