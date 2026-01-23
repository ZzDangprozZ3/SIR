# Projet SIR: Adaptation des Frameworks d’Anomalies au Dataset NetMob23

## Organisation

Ce dossier contient l'adaptation des 7 frameworks;
Chaque framework est contenue dans le dossier avec son nom repectif.
A la racine du projet doit etre ajouté un dossier **NetMob23** contenant les dossier des différentes applications et à la racine de celui-ci le fichier Lyon.geojson et les fichier de résultats de détéctions d'anomalies.

## Execution

Afin d'éxecuter un Framework il suffit de rester dans le dossier racine et d'éxecuter : **python main.py *nom du framework***

## Les différents frameworks

### Frameworks de detection d'anomalies

#### AWSCTD

Framework de détection d'anomalie supérvisé.
Nécessite l'ajout de label. Pour cela utilisez le fichier **anomalie.txt** dans le donssier AWSCTD

génère un fichier **ANOMALIE_REPORT.txt** dans le dossier *AWSCTD* que l'on peut utiliser pour les frameworks d'analyse cause racine.
le format est : Date: 20190501 | Tile: Facebook_DL_Tile_100006.txt | Confiance: 0.9267

##### Configuration d'AWSCTD

AWSCTD peu de configurer avec son fichier **config.ini** dans le dossier repectif.

**nMaxFiles** : Nombre de fichiers à traiter. Mettre None pour tout traiter.
**sModelName** : Architecture du réseau de neurones
Choix : FCN, LSTM-FCN, GRU-FCN, AWSCTD-CNN-S, AWSCTD-CNN-LSTM, AWSCTD-CNN-GRU, AWSCTD-CNN-D
**nEpochs** : Nombre d'itérations d'entraînement.
**nVocabSize** : Taille du vocabulaire après discrétisation (défaut: 100)
**nSequenceLengthLongueur** : des séquences temporelles (défaut: 96)
