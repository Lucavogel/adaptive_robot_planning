#!/usr/bin/env python3
"""
Script de test pour vérifier le modèle de détection d'émotions
"""

import sys
import os

def test_imports():
    """Teste les imports nécessaires"""
    print("Test des imports...")
    
    try:
        import cv2
        print("✓ OpenCV installé")
    except ImportError:
        print("✗ OpenCV manquant")
        return False
    
    try:
        import numpy as np
        print("✓ NumPy installé")
    except ImportError:
        print("✗ NumPy manquant")
        return False
    
    try:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        print("✓ Transformers installé")
    except ImportError:
        print("✗ Transformers manquant")
        return False
    
    try:
        import torch
        print("✓ PyTorch installé")
    except ImportError:
        print("✗ PyTorch manquant")
        return False
    
    try:
        from PIL import Image
        print("✓ Pillow installé")
    except ImportError:
        print("✗ Pillow manquant")
        return False
    
    return True

def test_camera():
    """Teste l'accès à la caméra"""
    print("\nTest de la caméra...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("✗ Impossible d'ouvrir la caméra")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("✗ Impossible de capturer une image")
            cap.release()
            return False
        
        print("✓ Caméra fonctionnelle")
        cap.release()
        return True
        
    except Exception as e:
        print(f"✗ Erreur caméra: {e}")
        return False

def test_model():
    """Teste le chargement du modèle"""
    print("\nTest du modèle...")
    
    try:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        
        print("Chargement du modèle (cela peut prendre du temps la première fois)...")
        processor = AutoImageProcessor.from_pretrained("dima806/facial_emotions_image_detection")
        model = AutoModelForImageClassification.from_pretrained("dima806/facial_emotions_image_detection")
        
        print("✓ Modèle chargé avec succès")
        print(f"✓ Classes disponibles: {list(model.config.id2label.values())}")
        return True
        
    except Exception as e:
        print(f"✗ Erreur modèle: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("=== Test du système de détection d'émotions ===\n")
    
    # Test des imports
    if not test_imports():
        print("\n❌ Certaines dépendances sont manquantes.")
        print("Exécutez: pip install -r requirements.txt")
        return False
    
    # Test de la caméra
    if not test_camera():
        print("\n❌ Problème avec la caméra.")
        print("Vérifiez qu'une caméra est connectée et accessible.")
        return False
    
    # Test du modèle
    if not test_model():
        print("\n❌ Problème avec le modèle.")
        print("Vérifiez votre connexion internet pour télécharger le modèle.")
        return False
    
    print("\n✅ Tous les tests sont passés!")
    print("Vous pouvez maintenant lancer: python3 emotion_detector.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
