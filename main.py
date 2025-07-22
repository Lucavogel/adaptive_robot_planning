#!/usr/bin/env python3

import rospy
from reasoning import reason_with_context
from perception import get_environment_context
from text_to_speech import speak
from aruco_arm_controller import ArucoArmController
import re

memory = []
exercise_sequence = [
    "Stretch your arms",
    "Touch your toes",
    "Rotate your neck"
]

def clean_for_speech(text):
    """
    Remove special commands (POINT_XXX, NEXT_EXERCISE:), markdown/code, and keep only user-facing output.
    """
    # Protection contre None
    if text is None:
        return ""
    
    # Convertir en string si nécessaire
    text = str(text)
    
    # NOUVEAU : Extraire seulement la partie Output
    output_match = re.search(r'Output:\s*(.+?)(?:\n|$)', text, re.DOTALL)
    if output_match:
        text = output_match.group(1).strip()
    
    # Remove markdown/code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"`+", "", text)
    # Remove command prefixes
    text = re.sub(r"^POINT_[A-Z_]+:? ?", "", text)
    text = re.sub(r"^NEXT_EXERCISE:? ?", "", text)
    text = re.sub(r"^STOP_ROUTINE:? ?", "", text)
    # Remove markdown formatting (bold, italics, etc)
    text = re.sub(r"[*_#>\[\]\(\)]", "", text)
    # Remove extra whitespace
    text = text.strip()
    # If the output is quoted, extract the quoted part
    match = re.match(r'"([^"]+)"', text)
    if match:
        text = match.group(1)
    return text

def extract_action_from_response(response):
    """Extraction robuste et généralisable des actions - VERSION SUPER CORRIGÉE"""
    if not response:
        return None
    
    # Normaliser le texte
    response_upper = response.upper()
    
    # 1. Recherche EXACTE des patterns POINT_ les plus courants d'abord
    exact_patterns = {
        "POINT_CELL_PHONE": "POINT_CELL_PHONE",
        "POINT_CUP": "POINT_CUP", 
        "POINT_DINING_TABLE": "POINT_DINING_TABLE",
        "POINT_LAPTOP": "POINT_LAPTOP",
        "POINT_BOTTLE": "POINT_BOTTLE",
        "POINT_CHAIR": "POINT_CHAIR",
        "POINTCELLPHONE": "POINT_CELL_PHONE",
        "POINTCUP": "POINT_CUP",
    }
    
    for pattern, action in exact_patterns.items():
        if pattern in response_upper:
            return action
    
    # 2. Patterns regex TRÈS RESTRICTIFS pour éviter la sur-capture
    point_patterns = [
        # Pattern pour POINT_WORD (un seul mot après POINT_)
        r'POINT_([A-Z][A-Z]*?)(?:\s|$|[.!?])',
        
        # Pattern pour POINT WORD WORD (maximum 2 mots)
        r'POINT\s+([A-Z]+\s+[A-Z]+)(?:\s|$|[.!?])',
        
        # Pattern pour POINTWORD (collé)
        r'POINT([A-Z]+)(?:\s|$|[.!?])',
    ]
    
    for pattern in point_patterns:
        match = re.search(pattern, response_upper)
        if match:
            object_name = match.group(1).strip()
            
            # Nettoyer l'objet
            object_name = re.sub(r'\s+', '_', object_name)
            object_name = object_name.rstrip('.,!?_')
            
            # Validation stricte des objets
            valid_objects = ['CELL_PHONE', 'CUP', 'DINING_TABLE', 'LAPTOP', 'BOTTLE', 'CHAIR', 'CELLPHONE']
            if object_name in valid_objects:
                # Normaliser CELLPHONE → CELL_PHONE
                if object_name == 'CELLPHONE':
                    object_name = 'CELL_PHONE'
                return f"POINT_{object_name}"
    
    # 3. Actions spéciales
    action_patterns = {
        r'STOP[_\s]*ROUTINE': 'STOP_ROUTINE',
        r'NEXT[_\s]*EXERCISE': 'NEXT_EXERCISE',
        r'START[_\s]*EXERCISE': 'START_EXERCISE',
    }
    
    for pattern, action in action_patterns.items():
        if re.search(pattern, response_upper):
            return action
    
    return None

def execute_llm_decision(action):
    """Exécuter une décision LLM avec le contrôleur de bras"""
    # Initialiser le contrôleur si nécessaire
    if not hasattr(execute_llm_decision, 'controller'):
        execute_llm_decision.controller = ArucoArmController()
    
    # Extraire l'objet à pointer
    if "POINT_" in action:
        obj_match = re.search(r"POINT_([A-Z_]+)", action)
        if obj_match:
            obj_name = obj_match.group(1).lower()
            # Mapper vers les noms d'objets YOLO
            object_mapping = {
                "cell_phone": "cell phone",
                "phone": "cell phone",
                "cup": "cup",
                "glass": "cup",
                "water": "cup", 
                "banana": "banana",
                "towel": "towel",
                "dining_table": "dining table",
                "table": "dining table",
                "chair": "chair",
                "laptop": "laptop",
                "bottle": "bottle"
            }
            yolo_name = object_mapping.get(obj_name, obj_name.replace('_', ' '))
            print(f"🎯 Mapping: {obj_name} → {yolo_name}")

            return execute_llm_decision.controller.point_to_object_with_aruco(yolo_name)
    
    return False

def normalize_object_name(action_object, detected_objects):
    """Normaliser et mapper les noms d'objets"""
    if not action_object:
        return None
    
    # Mapping des variations courantes
    object_mappings = {
        'CELL_PHONE': ['cell phone', 'phone', 'mobile'],
        'DINING_TABLE': ['dining table', 'table'],
        'CUP': ['cup', 'mug'],
        'BOTTLE': ['bottle', 'water bottle'],
        'LAPTOP': ['laptop', 'computer'],
        'CHAIR': ['chair', 'seat'],
        'PERSON': ['person', 'human'],
    }
    
    # Recherche directe
    for yolo_obj in detected_objects:
        obj_name = yolo_obj['name'].lower()
        
        # Match exact (après normalisation)
        if action_object.lower().replace('_', ' ') == obj_name:
            return obj_name
        
        # Match via mapping
        if action_object in object_mappings:
            if obj_name in object_mappings[action_object]:
                return obj_name
    
    # Fallback : recherche partielle
    for yolo_obj in detected_objects:
        obj_name = yolo_obj['name'].lower()
        if any(word in obj_name for word in action_object.lower().split('_')):
            return obj_name
    
    return None

def main():
    rospy.init_node("adaptive_coach", anonymous=True)
    dialogue_history = []
    
    print("Mode de raisonnement amélioré: ACTIVÉ")

    # Introduction
    intro_response = reason_with_context(
        context_description="",
        current_exercise="",
        next_exercise=exercise_sequence[0],
        dialogue_history=dialogue_history,
        user_input=""
    )
    
    print("intro :", intro_response)
    action = extract_action_from_response(intro_response)
    if action:
        spoken = clean_for_speech(action)
        if spoken:
            speak(spoken)
    else:
        # Pas d'action, utiliser la réponse complète pour la synthèse vocale
        spoken = clean_for_speech(intro_response)
        if spoken:
            speak(spoken)
    memory.append(action)
    dialogue_history.append(f"Robot: {clean_for_speech(intro_response)}")

    current_exercise_index = 0

    while current_exercise_index < len(exercise_sequence):
        exercise = exercise_sequence[current_exercise_index]
        print(f"\nExercice {current_exercise_index + 1}: {exercise}")
        next_exercise = exercise_sequence[current_exercise_index + 1] if current_exercise_index + 1 < len(exercise_sequence) else ""

        # Contexte environnemental
        perception_context = get_environment_context()
        print(perception_context)

        # Entrée utilisateur
        human_input = input("Human: ")
        if human_input:
            print(f"Human: {human_input}")
            dialogue_history.append(f"Human: {human_input}")
            
            # NOUVEAU : Détection manuelle de "stop" pour éviter les problèmes d'API
            stop_words = ["stop", "quit", "exit", "arrêt", "arreter", "stop routine", "enough"]
            if any(word in human_input.lower() for word in stop_words):
                print("🛑 Commande d'arrêt détectée manuellement (bypass API)")
                break  # Sort de la boucle while

        # Appel LLM avec système amélioré
        llm_response = reason_with_context(
            context_description=perception_context + "\n" + "\n".join(dialogue_history),
            current_exercise=exercise,
            next_exercise=next_exercise,
            dialogue_history=dialogue_history,
            user_input=human_input
        )
        
        print("\nRaisonnement du modèle:\n", llm_response)

        # CORRECTION ICI : Extraire l'action correctement
        action = extract_action_from_response(llm_response)
        
        if action:
            print(f" ###Robot Action#### {action}")
            
            if action.startswith('POINT_'):
                success = execute_llm_decision(action)
                if success:
                    print("✅ Mouvement réussi !")
                else:
                    print("❌ Échec du mouvement")
            elif action == 'NEXT_EXERCISE':
                current_exercise_index += 1
                print("⏭️ Exercice suivant")
                continue
            elif action == 'STOP_ROUTINE':
                print("🛑 Routine terminée par l'utilisateur")
                break  # Sort de la boucle while et termine la routine
        else:
            print(" ###Robot Action#### No action found.")

        # Synthèse vocale
        if action:
            spoken = clean_for_speech(action)
            if spoken:
                speak(spoken)
        else:
            # Pas d'action, utiliser la réponse LLM complète
            spoken = clean_for_speech(llm_response)
            if spoken:
                speak(spoken)

        memory.append(action)
        spoken_text = clean_for_speech(llm_response)
        dialogue_history.append(f"Robot: {spoken_text}")

    print("\nFin de la routine")
    print("\n############ Journal complet de la conversation #############")
    for line in dialogue_history:
        print(line)

    # Conclusion
    outro = reason_with_context(
        context_description="\n".join(dialogue_history),
        current_exercise="",
        next_exercise="",
        dialogue_history=dialogue_history,
        user_input=""
    )
    
    print("robot output:", outro)
    outro_action = extract_action_from_response(outro)
    outro_spoken = clean_for_speech(outro_action if outro_action else outro)
    if outro_spoken:
        speak(outro_spoken)
    dialogue_history.append(f"Robot: {outro}")

# Test de la fonction (pour debug)
def test_extract_action():
    """Tests pour vérifier le parsing"""
    test_cases = [
        "POINT_CELL_PHONE Sure!",
        "POINTCELLPHONE Sure!",
        "POINT CELL PHONE Sure!",
        "POINT TO CELL PHONE Sure!",
        "POINT_CUP Got it!",
        "POINTCUP Got it!",
        "POINT LAPTOP Please",
        "POINT TO DINING TABLE Please",
        "STOP_ROUTINE Goodbye!",
        "NEXT_EXERCISE Great!",
        "Output: POINT_DINING_TABLE Sure thing!"
    ]
    
    print("=== Test Parsing Amélioré ===")
    for test in test_cases:
        result = extract_action_from_response(test)
        print(f"'{test[:35]}...' → {result}")

if __name__ == "__main__":
    # Test rapide du parsing amélioré
    test_extract_action()
    
    print("\n=== Lancement normal ===")
    main()
