# TraceAnomaly – Version personnalisée pour NetMob

## 1️⃣ Présentation

`TraceAnomaly` est un **framework de détection d'anomalies** basé sur des traces réseau.  
Cette version a été **adaptée pour le dataset NetMob**, permettant d'analyser les données, détecter les anomalies et générer des rapports détaillés.

---

## 2️⃣ Dataset

- **Dataset utilisé :** NetMob (format CSV/JSON)  
- **Fichiers importants :**   
  - `TraceAnomaly/webankdata/rnvp_result` → répertoire où sont enregistrés les scores d'anomalies des timestamps
  - `TraceAnomaly/faults_TraceAnomaly.csv` →  répertoire où sont enregistrés les anomalies détectées

---

## 3️⃣ Structure du projet

```text
TraceAnomaly/
├── traceanomaly/             # package principale
│   ├── __init__.py
│   └── detection_anomaly.py
├── train_ticket/             # données initiales
├── webankdata/               # stocker les résultats
├── docker-compose.yml
├── Dockerfile
├── main.py               # à lancer
├── README.md
├── requirements.txt
└── traitementdata.py

```
## 4️⃣ Workflow

1. **Prétraitement des données**
   - Le script `traitementdata.py` est exécuté en premier.  
   - Il transforme les datasets au **format d'entrée attendu par le framework**.  
   - Résultat : des fichiers prêts pour l'entraînement et le scoring.

2. **Entraînement et scoring**
   - Utilisation de **Docker** pour lancer l'environnement complet :
   ```bash
   docker compose run --rm --build traceanomaly
   Le framework entraîne le modèle sur les données prétraitées.
    Pour chaque timestamp, il calcule le score de log-vraisemblance.
3. **Détection d'anomalies**
    - Le module `detection_anomaly.py` analyse les scores de log-vraisemblance.
    - Un timestamp est considéré comme anormal si son score est inférieur à la moyenne moins 2 fois l’écart-type.
    - Les anomalies détectées sont enregistrées dans `faults_TraceAnomaly.csv` pour analyse ultérieure.

## 5️⃣ Utilisation
python main.py

##### Configuration de TraceAnomaly 

TraceAnomaly est configurable via le fichier  
`TraceAnomaly/traceanomaly/main.py`