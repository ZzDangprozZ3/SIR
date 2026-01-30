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

Framework de détection d'anomalie supervisé. Nécessite l'ajout de label. Pour cela utilisez le fichier `anomalie.txt` dans le dossier `AWSCTD`.

Génère un fichier `AWSCTD_Anomaly_report_for_CausalRCA.txt` dans le dossier AWSCTD que l'on peut utiliser pour **causalRCA**.

Le format est : Date: 20190501 | Tile: Facebook_DL_Tile_100006.txt | Confiance: 0.9267

Génère en parralèle un fichier `AWSCTD_Anomaly_report_for_AlertRCA.csv` dans le dossier AWSCTD que l'on peut utiliser pour **AlertRCA**.

Le format est : id,score ; Facebook_100006_20190501,0.944564;

##### Configuration d'AWSCTD (AWSCTD/config.ini)

AWSCTD peut se configurer avec son fichier `config.ini` dans le dossier respectif.

- **nMaxFiles** : Nombre de fichiers à traiter. Mettre None pour tout traiter.
- **sModelName** : Architecture du réseau de neurones.
Choix : FCN, LSTM-FCN, GRU-FCN, AWSCTD-CNN-S, AWSCTD-CNN-LSTM, AWSCTD-CNN-GRU, AWSCTD-CNN-D
- **nEpochs** : Nombre d'itérations d'entraînement.
- **nVocabSize** : Taille du vocabulaire après discrétisation (défaut: 100).
- **nSequenceLength** : Longueur des séquences temporelles (défaut: 96)

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


#### AOC_IDS

Framework de détection d'anomalies basé sur l'apprentissage profond continu. Adapté au dataset NetMob23 pour la détection d'anomalies dans le trafic mobile.

Génère un fichier `anomalies_detected_all.csv` dans les dossiers `AOC_IDS/output/Facebook` et `AOC_IDS/output/Netflix` avec les prédictions.

Le format est : `tile_id,date,label_reel,label_predit`

Génère en parallèle un fichier `validation_report.txt` dans chaque dossier de service avec le rapport de validation croisée.

Le format du rapport inclut la distribution des anomalies détectées et le taux d'accord entre les méthodes.

##### Configuration d'AOC_IDS (AOC_IDS/run_complete_pipeline.sh)

AOC_IDS peut se configurer avec son fichier `run_complete_pipeline.sh` dans le dossier respectif.

* `--contamination` : Proportion d'anomalies pour la génération de pseudo-labels (défaut: 0.05)
* `--epochs` : Nombre d'itérations d'entraînement (défaut: 50)
* `--dataset` : Type de dataset (netmob pour NetMob23)

##### Workflow

1. **Extraction de features**
   * Exécution du script `convert.py`
   * Transformation des séries temporelles (96 points) en 15 features statistiques

2. **Génération de pseudo-labels**
   * Application d'un vote majoritaire entre 3 algorithmes : Isolation Forest, Z-Score, IQR
   * Labellisation binaire (0=normal, 1=anomalie)

3. **Entraînement et prédiction**
   * Lancement de l'environnement via Docker
   * Entraînement du modèle auto-encodeur avec CRC Loss
   * Génération des prédictions sur données de test

4. **Validation croisée**
   * Analyse comparative par le module `validation.py`

##### Sortie

* `AOC_IDS/output/{Service}/anomalies_detected_all.csv` : prédictions complètes par tile et date
* `AOC_IDS/output/{Service}/validation_report.txt` : rapport de cohérence des méthodes


### B. Frameworks d'analyse de la cause racine / RCA

#### CausalRCA

Framework utilisant des graphes causaux (DAG-GNN) pour identifier l'origine géographique d'une anomalie.

**Entrée** : Fichier **ANOMALY_REPORT.txt** et Lyon.geojson (à placer dans le dossier NetMob23).

**Sortie** : Rapports JSON par anomalie et matrice de causalité (dans le dossier `CausalRCA/data_collected`) *ET* **un rapport complet** de toute les causes racines pour chaque anomalie étudier dans le fichier `GLOBAL_RCA_RESULTS.csv` dans le dossier **NetMob23**

##### Configuration `CausalRCA/config.ini`

CausalRCA peut se configurer avec son fichier **config.ini** dans le dossier respectif.

- **anomalies_file** : Nom du fichier source.
- **top_n** : Nombre de voisins géographiques.
- **force_clean** : Nettoyage avant lancement.

#### AlertRCA

AlertRCA est un algorithme de RCA qui analyse automatiquement des alertes multimodales et construit un graphe de dépendances sans règles expertes ni traces coûteuses.

**Entrée** : 
- `faults_TraceAnomaly.csv` : anomalies détectées par TraceAnomaly  
- Fichiers de trafic `.txt` par service (Facebook, Netflix), granularité 15 minutes

**Fichiers intermédiaires** :
Générés par le script de prétraitement :
- `faults_alertRCA.csv`
- `faults.csv`
- `graph.yml`
- `train.csv`, `valid.csv`, `test.csv`
- `metrics_filtered.csv`
- `metrics.norm.csv`
- `anomaly_direction_constraint.json`

**Sortie** : 
- `AlertRCA/A_NetMob/report_alertRCA/report_A_NetMob.json`  
  Résultat final de l’analyse RCA (classement des causes racines - regionID et application)
  Le fichier `report_A_NetMob.json` contient, pour chaque timestamp UNIX, la cause racine réelle (`gt`) et le classement des nœuds candidats avec leur score et label (`fullResponse`).

#### Configuration de AlertRCA
AlertRCA est configurable via le fichier  
`AlertRCA/graph/deep_rule.py`

#### SGmVRNN

Framework de **détection d’anomalies non supervisé basé sur deep learning**, reposant sur un modèle variationnel récurrent (Stochastic Gated mVRNN), adapté au dataset **NetMob23**.

Il s’appuie sur :

- Un modèle séquentiel de type RNN/LSTM
- Un latent continu *z*
- Un latent catégoriel *c* estimé via Gumbel-Softmax
- Une génération probabiliste permettant le calcul d’un score par **log-vraisemblance**

Initialement conçu pour le dataset **SMD**, le framework a été adapté afin de fonctionner avec les données NetMob23.

##### Objectif de l’adaptation

- Conversion des données NetMob23 vers le format `.seq`
- Adaptation du modèle pour supporter `n = 96`
- Entraînement et génération de checkpoints
- Génération de scores exploitables pour la détection d’anomalies

---

##### Dataset NetMob23

Les données NetMob23 sont organisées par :

- Application (Facebook / Netflix / Spotify)
- Tuile géographique (Tile ID)
- Séries temporelles de trafic

Format des fichiers :

Chaque ligne commence par une date suivie de 96 valeurs (pas de 15 minutes → 24h) :
20190430 v1 v2 v3 ... v96


---

##### Difficultés rencontrées

###### (1) Incompatibilité du nombre de KPIs

Le modèle original ne supportait que :

- `n = 36` ou `n = 38`

Or NetMob nécessite :

- `n = 96`

**Solution** :

- Modification du fichier `model.py`
- Adaptation des modules `EncX` et `DecX`

---

###### (2) Incompatibilité des noms des fichiers `.seq`

Le loader `KpiReader` attend :

1.seq, 2.seq, 3.seq, ...


Après conversion NetMob :

100023.seq, 453162.seq, ...


**Solution** :

- Création d’un dataset renuméroté via liens symboliques

Exemple :

netmob_nf_dl_small_renum/train/1.seq → original/67.seq


---

###### (3) Instabilité numérique (NaN)

Les valeurs élevées du trafic (> 60000) provoquaient :

- Explosion de gradients
- NaN dès le premier epoch
- Sorties non finies

**Solution** :

Ajout d’une normalisation dans `trainer.py` :

- `log1p`
- Standardisation (mean/std)
- Clamp des valeurs

---

###### (4) Présence de valeurs NaN dans certaines applications

Certains fichiers (notamment Spotify) contenaient des NaN.

**Choix** :

- Priorisation des services Netflix et Facebook

---

##### Installation

###### 1. Création de l’environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate
```
###### 2. Installation des dépendances
```bash
pip install -r requirements.txt
```

##### Prétraitement : NetMob23 → .seq

SGmVRNN attend des fichiers `.seq` PyTorch contenant :

- **value** : tenseur `[20, 1, 96, 1]`
- **label** : tenseur `[20, 1, 1]`
- **ts** : tenseur `[20, 1, 1]`

Conversion via le script :

```bash
python scripts/netmob_to_seq.py \
  --input_path "data_preprocess/Dataset NetMob23/Netflix/DL" \
  --output_path "data_preprocess/data_processed/netmob_nf_dl/train" \
  --app netflix
```
##### Entraînement

Exemple d’entraînement sur NetMob (dataset renuméroté) :

```bash
python trainer.py \
  --dataset_path ../data_preprocess/data_processed/netmob_nf_dl_small_renum/train \
  --gpu_id 0 \
  --log_path log_trainer/netmob_nf_dl_small \
  --checkpoints_path model/netmob_nf_dl_small \
  --epochs 3 \
  --batch_size 128 \
  --n 96
```
Les checkpoints sont sauvegardés automatiquement dans le dossier model/

##### Résultats

Les résultats générés sont stockés dans :
```bash
results/netmob_nf_dl_small/netmob_nf_dl_small_scores.txt
```
Format :
```bash
timestamp, score_loglikelihood, Normaly/Anomaly
```

👉 Le score correspond à la log-vraisemblance du dernier timestamp.  
Plus la valeur est faible (négative), plus l’anomalie est probable.





