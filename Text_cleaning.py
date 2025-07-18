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
    # Clean up ** and strip lines
    cleaned = "\n".join(line.replace("**", "").strip() for line in llm_response.strip().splitlines())
    lines = [line for line in cleaned.splitlines()]

    for i, line in enumerate(lines):
        # Case: Output: (on its own line)
        if re.match(r"output\s*[:：]?\s*$", line, flags=re.IGNORECASE):
            # Return the first non-empty line after Output:
            for next_line in lines[i+1:]:
                next_line = next_line.strip()
                if next_line:
                    return next_line
        else:
            # Case: Output: on the same line
            match = re.match(r"output\s*[:：]?\s*(.+)", line, flags=re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    return content
            # Case: "✅ Robot Action:" (with or without stars/spaces)
            match_action = re.match(r"✅\s*robot action\s*[:：]?\s*(.*)", line, flags=re.IGNORECASE)
            if match_action:
                content = match_action.group(1).strip()
                if content:
                    return content

    return "No output found."



