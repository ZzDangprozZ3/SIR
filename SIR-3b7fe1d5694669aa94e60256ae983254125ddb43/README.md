# Projet SIR: Adaptation des Frameworks d’Anomalies au Dataset NetMob23

Ce dépôt contient :

- Le convertisseur du dataset NetMob23
- Les adaptations des frameworks étudiés
- Les Dockerfiles associés
- La documentation finale

## Membres du groupe

## Organisation

avant d'implémenter un convertisseur entre netmob23 et AWSCD, il faut commprendre comment les donné vont être transformer
Il faut, pour chaque framework avoir une validation.
la solution peu aussi être "peer reviewed"

### AWSCTD

#### Fonctionnement

Ce projet est une adaptation du framework de détection d'intrusions **AWSCTD** (initialement conçu pour les appels système Windows) appliqué à l'analyse de trafic mobile spatio-temporel (**NetMob23**).

Il utilise une architecture Dockerisée pour garantir la reproductibilité et l'indépendance de l'environnement.

#### Execution

##### Installation & Prérequis

Docker Desktop installé et lancé
Python 3.10+ (pour lancer l'orchestrateur main.py)

##### Prérequis

Créez un dossier NetMob23 à la racine SIR/
Déposez vos fichiers de trafic (.txt) à l'intérieur

##### Configuration

Tout le paramétrage se fait dans AWSCTD/config.ini sans toucher au code

**nMaxFiles** : Nombre de fichiers à traiter. Mettre None pour tout traiter.
**sModelName** : Architecture du réseau de neurones
Choix : AWSCTD-CNN-S (rapide), LSTM, GRU, etc.
**nEpochsNombre** :  d'itérations d'entraînement.

**nVocabSize** : Taille du vocabulaire après discrétisation (défaut: 100)
**nSequenceLengthLongueur** : des séquences temporelles (défaut: 96)

##### Utilisation

Ouvrez un terminal à la racine SIR/ et lancez :

Lancement standard :
python main.py AWSCTD

Forcer la reconstruction de l'image (si changement de requirements.txt) :
python main.py AWSCTD --rebuild

##### Étapes du Pipeline Automatisé

Build Docker : Crée une image isolée avec TensorFlow, Pandas, Scikit-learn.

Conversion : Le script convert_netmob_awsctd.py lit les fichiers .txt de NetMob23, les normalise (Log + MinMax) et génère un CSV prêt pour le modèle.

Entraînement : AWSCTD.py entraîne le modèle choisi (ex: CNN) en validation croisée (K-Fold).

Détection : Le modèle génère des alertes sur les séquences anormales.

Rapport : Un fichier ANOMALY_REPORT.txt est généré dans le dossier AWSCTD/.
