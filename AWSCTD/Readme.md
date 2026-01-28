# AWSCTD : Adaptation pour NetMob23

Ce module est une adaptation du framework **AWSCTD** (Anomaly detection in Web Service traffic) pour détecter des anomalies dans les données de trafic mobile du dataset **NetMob23**.

Il s'agit d'une approche **supervisée** utilisant des réseaux de neurones profonds (CNN, LSTM, GRU) pour classifier des séquences temporelles de trafic.

## Configuration (config.ini)

Tout le comportement du framework se pilote ici.
Ne modifiez pas le code, modifiez ce fichier.

### Section [DATA]

**nMaxFiles :** Limite le nombre de fichiers bruts traités (None pour aucune limite)
**nSequenceLength :** Longueur des fenêtres temporelles (auto-detection est au cas ou utilisé)
**nVocabSize :** Taille de discrétisation (nombre de classes de volume)

### Section [MODEL]

**ModelName :** Architecture du réseau
Choix : FCN, LSTM-FCN, GRU-FCN, AWSCTD-CNN-S, AWSCTD-CNN-LSTM, AWSCTD-CNN-GRU, AWSCTD-CNN-D
**nEpochs :** Nombre d'itérations d'entraînement

### Section [FILES]

Définit les noms des fichiers d'entrée/sortie

## Gestion des Labels (anomalie.txt)

Puisque c'est une méthode supervisée, AWSCTD a besoin de savoir ce qui est une anomalie pour apprendre. Vous devez remplir le fichier anomalie.txt avec les périodes et les tuiles considérées comme anormales.
Format du fichier : Chaque ligne correspond à un critère
20190501 : Cette date contient des anomalies
Facebook_DL_Tile_100006.txt : Cette tuile spécifique est anormale (peu importe la date)

## Structure du Dossier

Voici les fichiers clés pour comprendre le fonctionnement du module :

```text
AWSCTD/
├── config.ini                  # FICHIER DE CONFIGURATION PRINCIPAL
├── anomalie.txt                # Fichier de labels (Vérité terrain pour l'entraînement)
│
├── pipeline.sh                 # Script d'entrée pour le conteneur Docker
├── convert_netmob-awsctd.py    # Script de conversion des données brutes NetMob -> CSV
├── AWSCTD.py                   # Script principal d'entraînement du modèle
├── AWSCTD_Detect.py            # Script de détection et génération de rapports
├── requirements.txt            # Dépendances Python
├── dockerfile                  # Définition de l'image Docker
├── Utils/                      # Fonctions utilitaires (Plot, Matrices de confusion)
│   ├── AWSCTDgeneratedimage.py
│   ├── AwsctdPlotACC.py
│   └── AWSCTDplotCM.py
└── workflow/                   # Dossier de travail temporaire (données intermédiaires)
```

## Workflow

Le pipeline complet est automatisé, mais voici ce qui se passe en détail :

### 1. Conversion des Données (convert_netmob_awsctd.py)

1. Lit les données brutes dans ../NetMob23.
2. Génère le fichiers de données pour le réseau de neurones :
    - Les séquences de trafic discrétisée *netmob_for_awsctd.csv*
    - Les métadonnées associées *netmob_metadata.csv*

### 2. Entraînement (AWSCTD.py)

1. Charge les données converties et les labels depuis **anomalie.txt**
2. Entraîne le modèle défini dans config.ini
3. Sauvegarde le modèle entraîné sous trained_model.keras.
4. Génère les courbes d'apprentissage dans ACCLOSS/ et les matrices de confusion dans CM/

### 3. Détection & Rapport (AWSCTD_Detect.py)

1. harge le modèle sauvegardé
2. Relance une prédiction sur l'ensemble des données
3. Génère deux rapports de sortie (voir section Sorties)

## Sorties Générées

À la fin de l'exécution, vous récupérerez :

un **fichier txt** pour **causalrca** au format :
Date: 20190512 | Tile: Facebook_DL_Tile_100006.txt | Confiance: 0.9992

un **fichier csv** pour **alertrca** au format :
id,score
Facebook_100006_20190512,0.999200

Graphiques :ACCLOSS/*.svg : Courbes de précision et de perte (Loss)
CM/*.svg : Matrices de confusion (Performance du modèle)

## Forcer la reconstruction de l'image Docker (si modification de code)

python main.py awsctd --rebuild
