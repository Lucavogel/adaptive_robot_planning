import re


def clean_llm_response(text: str) -> str:
    text = re.sub(r'[\*"]+', '', text)  # Supprime guillemets et **
    text = text.strip()
    text = re.sub(r'^POINT_[A-Z_]+\s*', '', text)
    text = re.sub(r'^NEXT_EXERCISE:\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^STOP_ROUTINE\s*', '', text, flags=re.IGNORECASE)
    return text.strip()





def extract_action_from_response(llm_response: str) -> str:
    
    cleaned = "\n".join(line.replace("**", "").strip() for line in llm_response.strip().splitlines())
    lines = [line for line in cleaned.splitlines()]
    output_found = False

    for i, line in enumerate(lines):
       
        if re.match(r"output\s*[:：]?\s*$", line, flags=re.IGNORECASE):
            output_found = True
            for next_line in lines[i+1:]:
                next_line = next_line.strip()
                if next_line and not next_line.lower().startswith("robot action"):
                    return next_line
        else:
           
            match = re.match(r"output\s*[:：]?\s*(.+)", line, flags=re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    return content
           
            match_action = re.match(r"\s*robot action\s*[:：]?\s*(.*)", line, flags=re.IGNORECASE)
            if match_action:
                content = match_action.group(1).strip()
                if content:
                    return content

    return "No output found."



