#!/usr/bin/env python3
"""
Détection d'émotions en temps réel avec la caméra
Utilise le modèle dima806/facial_emotions_image_detection
"""

import cv2
import numpy as np
from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch
from PIL import Image
import time

class EmotionDetector:
    def __init__(self):
        """Initialise le détecteur d'émotions"""
        print("Chargement du modèle de détection d'émotions...")
        
        # Charger le modèle et le processeur
        self.processor = AutoImageProcessor.from_pretrained("dima806/facial_emotions_image_detection")
        self.model = AutoModelForImageClassification.from_pretrained("dima806/facial_emotions_image_detection")
        
        # Initialiser la caméra
        self.cap = cv2.VideoCapture(0)
        
        # Vérifier si la caméra est disponible
        if not self.cap.isOpened():
            raise Exception("Impossible d'ouvrir la caméra")
        
        # Configurer la caméra
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Charger le classificateur de visages de OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Variables pour l'affichage
        self.current_emotion = "Aucune détection"
        self.confidence = 0.0
        self.last_detection_time = time.time()
        
        print("Modèle chargé avec succès!")
        print("Appuyez sur 'q' pour quitter")
    
    def preprocess_face(self, face_image):
        """Prétraite l'image du visage pour le modèle"""
        # Convertir en PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB))
        
        # Utiliser le processeur du modèle
        inputs = self.processor(pil_image, return_tensors="pt")
        return inputs
    
    def predict_emotion(self, face_image):
        """Prédit l'émotion à partir d'une image de visage"""
        try:
            # Prétraiter l'image
            inputs = self.preprocess_face(face_image)
            
            # Faire la prédiction
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Obtenir l'émotion prédite
            predicted_class_id = predictions.argmax().item()
            confidence = predictions.max().item()
            
            # Mapper l'ID de classe au nom de l'émotion
            emotion_label = self.model.config.id2label[predicted_class_id]
            
            return emotion_label, confidence
        
        except Exception as e:
            print(f"Erreur lors de la prédiction: {e}")
            return "Erreur", 0.0
    
    def detect_faces(self, frame):
        """Détecte les visages dans une frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        return faces
    
    def draw_results(self, frame, faces):
        """Dessine les résultats sur la frame"""
        for (x, y, w, h) in faces:
            # Dessiner le rectangle autour du visage
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Extraire la région du visage
            face_roi = frame[y:y+h, x:x+w]
            
            # Prédire l'émotion si le visage est assez grand
            if w > 50 and h > 50:
                emotion, confidence = self.predict_emotion(face_roi)
                self.current_emotion = emotion
                self.confidence = confidence
                self.last_detection_time = time.time()
                
                # Afficher l'émotion et la confiance
                text = f"{emotion}: {confidence:.2f}"
                cv2.putText(frame, text, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Afficher les informations générales
        info_text = f"Emotion actuelle: {self.current_emotion} ({self.confidence:.2f})"
        cv2.putText(frame, info_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Afficher le temps depuis la dernière détection
        time_since_detection = time.time() - self.last_detection_time
        time_text = f"Derniere detection: {time_since_detection:.1f}s"
        cv2.putText(frame, time_text, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def run(self):
        """Lance la détection en temps réel"""
        print("Détection d'émotions en cours...")
        
        try:
            while True:
                # Capturer une frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Impossible de capturer la frame")
                    break
                
                # Détecter les visages
                faces = self.detect_faces(frame)
                
                # Dessiner les résultats
                frame = self.draw_results(frame, faces)
                
                # Afficher la frame
                cv2.imshow('Detection d\'emotions en temps reel', frame)
                
                # Vérifier si l'utilisateur veut quitter
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        except KeyboardInterrupt:
            print("\nArrêt demandé par l'utilisateur")
        
        finally:
            # Nettoyer
            self.cleanup()
    
    def cleanup(self):
        """Nettoie les ressources"""
        print("Nettoyage des ressources...")
        self.cap.release()
        cv2.destroyAllWindows()
        print("Terminé!")

def main():
    """Fonction principale"""
    try:
        detector = EmotionDetector()
        detector.run()
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    main()
