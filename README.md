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

### B. Frameworks de détection d'anomalies / RCA

#### CausalRCA

Framework utilisant des graphes causaux (DAG-GNN) pour identifier l'origine géographique d'une anomalie.

**Entrée** : Fichier ANOMALY_REPORT.txt et Lyon.geojson (à placer dans le dossier NetMob23).

**Sortie** : Rapports JSON par anomalie et matrice de causalité (dans le dossier CausalRCA).

#### Configuration (CausalRCA/config.ini)

CausalRCA peut se configurer avec son fichier **config.ini** dans le dossier respectif.

**anomalies_file** : Nom du fichier source.
**top_n** : Nombre de voisins géographiques.
**force_clean** : Nettoyage avant lancement.
