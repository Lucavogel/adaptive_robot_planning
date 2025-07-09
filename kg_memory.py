class ExerciseHistory:
    def __init__(self):
        self.exercise_records = {}  # ex: {"ArmRaise": {"emotion": "Tired", "duration": 7.2}}

    def add_record(self, exercise_name: str, emotion: str, duration: float):
        self.exercise_records[exercise_name] = {
            "emotion": emotion,
            "duration": round(duration, 2)  # arrondi à 2 chiffres
        }

    def get_emotion(self, exercise_name):
        return self.exercise_records.get(exercise_name, {}).get("emotion", "Unknown")

    def get_duration(self, exercise_name):
        return self.exercise_records.get(exercise_name, {}).get("duration", None)

    def format_as_text(self):
        if not self.exercise_records:
            return "No exercise history yet."
        lines = []
        for ex, data in self.exercise_records.items():
            line = f"During '{ex}', user felt {data['emotion']}"
            if data["duration"] is not None:
                line += f" and completed it in {data['duration']} seconds."
            lines.append(line)
        return "\n".join(lines)


import re

def extract_user_emotion(user_input: str) -> str:
    # Très simple pour tester, tu peux améliorer ensuite
    patterns = {
        "tired": ["tired", "exhausted", "low energy"],
        "motivated": ["ready", "motivated", "great"],
        "in pain": ["pain", "hurts", "sore"],
        "frustrated": ["annoyed", "frustrated", "not working"],
        "happy": ["happy", "good", "nice", "smiling"]
    }

    user_input = user_input.lower()
    for emotion, keywords in patterns.items():
        for word in keywords:
            if re.search(rf"\b{word}\b", user_input):
                return emotion.capitalize()
    return "Unknown"