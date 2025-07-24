# Détection d'Émotions en Temps Réel

Ce dossier contient un système de détection d'émotions en temps réel utilisant la caméra et le modèle `dima806/facial_emotions_image_detection`.

## Fonctionnalités

- Détection de visages en temps réel avec OpenCV
- Classification d'émotions avec un modèle de deep learning
- Interface visuelle avec affichage des résultats
- Support de plusieurs visages simultanément

## Installation

### 1. Installation automatique
```bash
chmod +x install.sh
./install.sh
```

### 2. Installation manuelle
```bash
pip install -r requirements.txt
```

## Utilisation

### 1. Test du système
Avant la première utilisation, testez que tout fonctionne :
```bash
python3 test_setup.py
```

### 2. Lancement de la détection
```bash
python3 emotion_detector.py
```

### Contrôles
- Appuyez sur **'q'** pour quitter
- Le système détecte automatiquement les visages et affiche les émotions

## Émotions Détectées

Le modèle peut détecter les émotions suivantes :
- Angry (Colère)
- Disgust (Dégoût)
- Fear (Peur)
- Happy (Joie)
- Neutral (Neutre)
- Sad (Tristesse)
- Surprise (Surprise)

## Configuration Système

### Prérequis
- Python 3.6+
- Caméra USB ou webcam intégrée
- Connexion internet (pour le premier téléchargement du modèle)

### Dépendances
- OpenCV (cv2) : Capture vidéo et détection de visages
- Transformers : Modèle de classification d'émotions
- PyTorch : Framework de deep learning
- NumPy : Calculs numériques
- Pillow : Traitement d'images

## Dépannage

### Problème de caméra
Si la caméra n'est pas détectée :
```bash
# Vérifier les caméras disponibles
ls /dev/video*

# Tester avec une autre caméra
# Modifier la ligne dans emotion_detector.py :
# self.cap = cv2.VideoCapture(1)  # Essayer 1, 2, etc.
```

### Problème de performance
Si le système est lent :
- Réduire la résolution de la caméra
- Utiliser un GPU si disponible (CUDA)
- Ajuster la fréquence de détection

### Problème de modèle
Si le modèle ne se télécharge pas :
- Vérifier la connexion internet
- Vider le cache : `rm -rf ~/.cache/huggingface/`

## Architecture du Code

```
emotion_detection/
├── emotion_detector.py     # Script principal
├── test_setup.py          # Tests du système
├── install.sh             # Installation automatique
├── requirements.txt       # Dépendances Python
└── README.md             # Cette documentation
```

### Classes principales

- **EmotionDetector** : Classe principale pour la détection
  - `__init__()` : Initialisation du modèle et caméra
  - `detect_faces()` : Détection de visages avec OpenCV
  - `predict_emotion()` : Prédiction d'émotion avec le modèle
  - `run()` : Boucle principale de détection
  - `cleanup()` : Nettoyage des ressources

## Personnalisation

### Modifier la résolution de la caméra
```python
self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # Largeur
self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)   # Hauteur
```

### Changer le seuil de confiance
```python
if confidence > 0.7:  # Afficher seulement si confiance > 70%
    # Afficher l'émotion
```

### Utiliser un autre modèle
Remplacer les lignes de chargement du modèle :
```python
self.processor = AutoImageProcessor.from_pretrained("votre_modele")
self.model = AutoModelForImageClassification.from_pretrained("votre_modele")
```

## Performance

- **Temps de réponse** : ~50-100ms par frame
- **Précision** : Variable selon l'éclairage et la qualité de l'image
- **Ressources** : ~500MB RAM, CPU/GPU selon la configuration

## Licence

Ce code utilise le modèle `dima806/facial_emotions_image_detection` sous licence MIT.
