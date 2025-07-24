# Configuration MoveIt pour Lynx SES900

## Fichiers générés

1. **joint_limits.json** - Limites des joints et vitesses
2. **ompl_planning.json** - Configuration des planificateurs OMPL
3. **kinematics.json** - Configuration du solveur cinématique
4. **controllers.json** - Configuration des contrôleurs
5. **lynx_ses900.srdf** - Fichier SRDF avec groupes et états

## Utilisation

### Lancement avec MoveIt

```bash
roslaunch lynx_moveit_config move_group.launch
```

### États prédéfinis

- **home**: Position neutre (tous joints à 0)
- **ready**: Position prête pour manipulation

### Groupes de planification

- **manipulator**: Chaîne cinématique complète
- **end_effector**: Effecteur terminal uniquement

### Recommandations

1. **Zone de travail optimale**: < 0.69 m du centre
2. **Zone de travail sûre**: < 0.83 m du centre
3. **Portée maximale**: 0.98 m

### Paramètres de sécurité

- Vitesse maximale réduite à 10% par défaut
- Accélération limitée à 10% par défaut
- Planification avec timeout de 5 secondes

## Calibration requise

Avant utilisation, effectuer:
1. Calibration des joints
2. Vérification des limites
3. Test de l'espace de travail
4. Validation des collisions

## Support

Basé sur l'analyse de l'espace de travail du Lynx SES900.
Voir les fichiers d'analyse pour plus de détails.
