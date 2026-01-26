# Projet SIR : Adaptation des Frameworks d’Anomalies au Dataset NetMob23

Ce projet vise à adapter et exécuter 7 frameworks de détection d'anomalies et d'analyse de cause racine sur les données de trafic mobile du dataset NetMob23.

## 1. Organisation des Données

Le projet repose sur une structure de fichiers stricte pour assurer le bon fonctionnement des conteneurs Docker.

### Structure requise

Pour assurer le bon fonctionnement du code, vous devez organiser vos fichiers selon l'arborescence suivante à la racine du projet :

```text
.
└── NetMob23/
    ├── Netflix/
    │   └── data_netflix.txt
    ├── Facebook/
    │   └── data_facebook.txt
    ├── Lyon.geojson
    ├── anomalie_pour_CausalRCA.txt
    └── anomalie_pour_AlertRCA.csv
```

## 2. Exécution

L'exécution est centralisée via le script **main.py** qui gère la construction des images Docker et le lancement des pipelines.

### Commande principale

Depuis la racine du projet : **python main.py <nom_du_framework>**

### Options disponibles

Reconstruction forcée : Si vous avez modifié le code ou le Dockerfile, forcez la reconstruction de l'image : **python main.py awsctd --rebuild**

## 3. Détail des Frameworks

### A. Frameworks de détection d'anomalies

#### AWSCTD

Framework de détection d'anomalie supervisé. Nécessite l'ajout de label. Pour cela utilisez le fichier anomalie.txt dans le dossier AWSCTD.

Génère un fichier ANOMALY_REPORT.txt dans le dossier AWSCTD que l'on peut utiliser pour les frameworks d'analyse cause racine. 
Le format est : Date: 20190501 | Tile: Facebook_DL_Tile_100006.txt | Confiance: 0.9267

##### Configuration d'AWSCTD (AWSCTD/config.ini)

AWSCTD peut se configurer avec son fichier config.ini dans le dossier respectif.

**nMaxFiles** : Nombre de fichiers à traiter. Mettre None pour tout traiter.
**sModelName** : Architecture du réseau de neurones.
Choix : FCN, LSTM-FCN, GRU-FCN, AWSCTD-CNN-S, AWSCTD-CNN-LSTM, AWSCTD-CNN-GRU, AWSCTD-CNN-D
**nEpochs** : Nombre d'itérations d'entraînement.
**nVocabSize** : Taille du vocabulaire après discrétisation (défaut: 100).
**nSequenceLength** : Longueur des séquences temporelles (défaut: 96)

#### TraceAnomaly
Framework de **détection d’anomalies basé sur des traces réseau**, adapté au dataset **NetMob**.

##### Configuration de TraceAnomaly 

TraceAnomaly est configurable via le fichier  
`TraceAnomaly/traceanomaly/main.py`

##### Workflow

###### 1. Prétraitement des données
- Exécution du script `traitementdata.py`
- Transformation des données NetMob vers le **format d’entrée attendu par le framework**

###### 2. Entraînement et scoring
- Lancement de l’environnement via **Docker**
- Entraînement du modèle
- Calcul d’un **score de log-vraisemblance** pour chaque timestamp

###### 3. Détection d’anomalies
- Analyse des scores par le module `detection_anomaly.py`

**Sortie** :  
  - `TraceAnomaly/webankdata/rnvp_result` : scores d’anomalies par timestamp
  - `TraceAnomaly/faults_TraceAnomaly.csv` : anomalies détectées
Le format du fichier est le suivant : id,score | Netflix_45541_20190508,-4.5588937

### B. Frameworks d'analyse de la cause racine / RCA

#### CausalRCA

Framework utilisant des graphes causaux (DAG-GNN) pour identifier l'origine géographique d'une anomalie.

**Entrée** : Fichier ANOMALY_REPORT.txt et Lyon.geojson (à placer dans le dossier NetMob23).

**Sortie** : Rapports JSON par anomalie et matrice de causalité (dans le dossier CausalRCA).

#### Configuration (CausalRCA/config.ini)

CausalRCA peut se configurer avec son fichier **config.ini** dans le dossier respectif.

**anomalies_file** : Nom du fichier source.
**top_n** : Nombre de voisins géographiques.
**force_clean** : Nettoyage avant lancement.
