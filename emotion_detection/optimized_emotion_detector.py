#!/usr/bin/env python3
"""
Détecteur d'émotions ultra-rapide - Version corrigée
"""

import cv2
import numpy as np
from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch
from PIL import Image
import time

class UltraFastEmotionDetector:
    def __init__(self):
        print("🔄 Chargement ultra-rapide...")
        
        # Configuration device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"📱 Utilisation: {self.device}")
        
        # Charger le modèle SANS optimisations problématiques
        self.processor = AutoImageProcessor.from_pretrained("dima806/facial_emotions_image_detection")
        self.model = AutoModelForImageClassification.from_pretrained("dima806/facial_emotions_image_detection")
        self.model.to(self.device)
        self.model.eval()
        
        # Pré-calculer les paramètres de normalisation
        self.mean = torch.tensor([0.485, 0.456, 0.406]).to(self.device).view(1, 3, 1, 1)
        self.std = torch.tensor([0.229, 0.224, 0.225]).to(self.device).view(1, 3, 1, 1)
        
        # Caméra optimisée
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("❌ Caméra non disponible")
            
        # Paramètres caméra pour vitesse
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        self.cap.set(cv2.CAP_PROP_FPS, 15)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Détecteur de visage rapide
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Variables d'état
        self.emotions = {
            'happy': 'happy😊', 'sad': 'sad😢', 'angry': 'angry😠',
            'fear': 'fear😨', 'surprise': 'surprise😮', 'disgust': 'disgust🤢', 'neutral': 'neutral😐'
        }
        
        self.current_emotion = "🔍"
        self.current_confidence = 0.0
        self.skip_frames = 2  # Analyser 1 frame sur 2
        self.frame_counter = 0
        
        print("✅ Prêt pour détection rapide!")

    def fast_predict(self, face_image):
        """Prédiction optimisée"""
        try:
            # Redimensionner et convertir
            face_resized = cv2.resize(face_image, (224, 224))
            face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
            
            # Convertir en tensor et normaliser
            face_tensor = torch.from_numpy(face_rgb).float().to(self.device)
            face_tensor = face_tensor.permute(2, 0, 1).unsqueeze(0) / 255.0
            
            # Normalisation standard ImageNet
            face_tensor = (face_tensor - self.mean) / self.std
            
            # Prédiction rapide
            with torch.no_grad():
                outputs = self.model(face_tensor)
                probs = torch.softmax(outputs.logits, dim=-1)
                max_prob, predicted = torch.max(probs, 1)
            
            # Récupérer résultats
            emotion_id = predicted.item()
            confidence = max_prob.item()
            emotion_name = self.model.config.id2label[emotion_id]
            
            return emotion_name, confidence
            
        except Exception as e:
            print(f"\n❌ Erreur prédiction: {e}")
            return "error", 0.0

    def run(self):
        """Boucle principale ultra-rapide"""
        print("🎥 Démarrage détection temps réel...")
        print("Press Ctrl+C pour arrêter\n")
        
        try:
            while True:
                # Lire frame
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Erreur lecture caméra")
                    break
                
                self.frame_counter += 1
                
                # Traiter seulement certaines frames
                if self.frame_counter % self.skip_frames == 0:
                    # Détection visage sur frame réduite
                    small_frame = cv2.resize(frame, (240, 180))
                    gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                    
                    # Détecter visages
                    faces = self.face_cascade.detectMultiScale(
                        gray, 
                        scaleFactor=1.2, 
                        minNeighbors=3, 
                        minSize=(40, 40)
                    )
                    
                    if len(faces) > 0:
                        # Plus grand visage
                        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
                        x, y, w, h = largest_face
                        
                        # Redimensionner coordonnées pour frame original
                        scale_x = frame.shape[1] / 240
                        scale_y = frame.shape[0] / 180
                        
                        x = int(x * scale_x)
                        y = int(y * scale_y)
                        w = int(w * scale_x)
                        h = int(h * scale_y)
                        
                        # Extraire visage avec marge
                        margin = 15
                        x1 = max(0, x - margin)
                        y1 = max(0, y - margin)
                        x2 = min(frame.shape[1], x + w + margin)
                        y2 = min(frame.shape[0], y + h + margin)
                        
                        face_roi = frame[y1:y2, x1:x2]
                        
                        if face_roi.size > 0:
                            # Prédire émotion
                            emotion, confidence = self.fast_predict(face_roi)
                            
                            # Mettre à jour si confiance suffisante
                            if confidence > 0.3:
                                self.current_emotion = self.emotions.get(emotion, "❓")
                                self.current_confidence = confidence
                    else:
                        # Aucun visage détecté
                        if self.current_confidence > 0:
                            self.current_confidence *= 0.9  # Diminuer progressivement
                
                # Affichage en temps réel
                if self.current_confidence > 0.2:
                    print(f"\r{self.current_emotion} {self.current_confidence:.0%}    ", end="", flush=True)
                else:
                    print(f"\r🔍 Recherche visage...    ", end="", flush=True)
                
                # Petite pause pour éviter surcharge CPU
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Arrêt demandé")
        
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
        
        finally:
            self.cap.release()
            print("✅ Nettoyage terminé!")

def main():
    """Point d'entrée"""
    try:
        detector = UltraFastEmotionDetector()
        detector.run()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")

if __name__ == "__main__":
    main()