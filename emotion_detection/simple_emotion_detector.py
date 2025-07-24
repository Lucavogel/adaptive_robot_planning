#!/usr/bin/env python3
"""
Version simplifiée de la détection d'émotions en temps réel
Affiche uniquement les émotions détectées dans le terminal
"""

import cv2
import numpy as np
from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch
from PIL import Image
import time
import threading

class SimpleEmotionDetector:
    def __init__(self):
        """Initialise le détecteur simple"""
        print("🔄 Chargement du modèle...")
        
        # Charger le modèle et le processeur
        self.processor = AutoImageProcessor.from_pretrained("dima806/facial_emotions_image_detection")
        self.model = AutoModelForImageClassification.from_pretrained("dima806/facial_emotions_image_detection")
        
        # Initialiser la caméra
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("❌ Impossible d'ouvrir la caméra")
        
        # Charger le classificateur de visages
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Variables
        self.current_emotion = "Aucune détection"
        self.confidence = 0.0
        self.running = True
        
        print("✅ Modèle chargé! Appuyez sur Ctrl+C pour quitter")
    
    def predict_emotion(self, face_image):
        """Prédit l'émotion"""
        try:
            # Convertir en PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB))
            
            # Prétraiter
            inputs = self.processor(pil_image, return_tensors="pt")
            
            # Prédire
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Résultats
            predicted_class_id = predictions.argmax().item()
            confidence = predictions.max().item()
            emotion_label = self.model.config.id2label[predicted_class_id]
            
            return emotion_label, confidence
        
        except Exception as e:
            return "Erreur", 0.0
    
    def display_emotion_info(self):
        """Affiche les informations d'émotion dans le terminal"""
        while self.running:
            if self.confidence > 0.5:  # Seulement si confiance > 50%
                emotion_map = {
                    'happy': '😊 Joie',
                    'sad': '😢 Tristesse', 
                    'angry': '😠 Colère',
                    'fear': '😨 Peur',
                    'surprise': '😮 Surprise',
                    'disgust': '🤢 Dégoût',
                    'neutral': '😐 Neutre'
                }
                
                emotion_display = emotion_map.get(self.current_emotion, f"📊 {self.current_emotion}")
                print(f"\r{emotion_display} ({self.confidence:.1%}) ", end="", flush=True)
            else:
                print(f"\r🔍 Recherche de visage... ", end="", flush=True)
            
            time.sleep(1)
    
    def run(self):
        """Lance la détection"""
        # Démarrer l'affichage en arrière-plan
        display_thread = threading.Thread(target=self.display_emotion_info)
        display_thread.daemon = True
        display_thread.start()
        
        try:
            print("\n🎥 Détection en cours...")
            
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                
                # Détecter les visages
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(50, 50))
                
                if len(faces) > 0:
                    # Prendre le plus grand visage
                    largest_face = max(faces, key=lambda face: face[2] * face[3])
                    x, y, w, h = largest_face
                    
                    # Extraire et analyser
                    face_roi = frame[y:y+h, x:x+w]
                    emotion, confidence = self.predict_emotion(face_roi)
                    
                    self.current_emotion = emotion
                    self.confidence = confidence
                else:
                    self.confidence = 0.0
                
                time.sleep(1)  # Petite pause pour éviter la surcharge
        
        except KeyboardInterrupt:
            print("\n\n🛑 Arrêt demandé par l'utilisateur")
        
        finally:
            self.running = False
            self.cap.release()
            print("\n✅ Nettoyage terminé!")

def main():
    """Fonction principale"""
    try:
        detector = SimpleEmotionDetector()
        detector.run()
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
