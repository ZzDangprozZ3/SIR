# SGmVRNN – Adaptation au dataset NetMob23 (Projet SIR)

Ce dépôt contient mon travail réalisé dans le cadre du **projet SIR** :  
➡️ **Intégration + adaptation du framework SGmVRNN** (*Stochastic Gumbel Variational RNN*) pour la **détection d’anomalies sur séries temporelles**, appliquée au dataset **NetMob23**.

L’objectif principal demandé était : **faire tourner le framework sur NetMob23 et produire des résultats (scores d’anomalie)**.

---

## 1) Contexte et objectif

### Framework
**SGmVRNN** est un modèle deep learning non supervisé basé sur :
- un modèle séquentiel de type **RNN/LSTM**
- un latent continu **z**
- un latent catégoriel **c** estimé via **Gumbel-Softmax**
- une génération probabiliste qui permet de calculer un score basé sur la **log-vraisemblance**

Le framework est initialement conçu pour le dataset **SMD** (Server Machine Dataset), avec un format très strict.

### Objectif de mon travail
Adapter SGmVRNN pour fonctionner sur **NetMob23** :
- conversion des données NetMob23 vers le format `.seq` attendu par SGmVRNN
- adaptation du modèle pour supporter `n=96` (NetMob)
- entraînement + génération de checkpoints
- test et génération de **scores** (loglikelihood) exploitable

---

## 2) Dataset NetMob23

NetMob23 contient des fichiers texte de trafic réseau mobile structurés par :
- **application** (Facebook / Netflix / Spotify)
- **tuile géographique** (Tile ID)
- valeurs temporelles (trafic)

### Format (exemple)
Chaque ligne du fichier :
- commence par une date `YYYYMMDD`
- suivie par **96 valeurs** (pas temporel de 15 minutes → 24h)

Exemple :
20190430 v1 v2 v3 ... v96


---

## 3) Difficultés rencontrées

### (1) Incompatibilité du nombre de KPIs `n`
Le modèle original SGmVRNN ne supporte que :
- `n=36` ou `n=38` (hardcodé dans le CNN encoder/decoder)

Or NetMob nécessite :
- `n=96`

✅ Solution :
- modification du `model.py` pour permettre `n=96`  
(EncX et DecX adaptés)

---

### (2) Nom des fichiers `.seq` non compatible
Le loader `KpiReader` lit les fichiers sous la forme :
- `1.seq`, `2.seq`, `3.seq`, ...

Mais après conversion NetMob :
- noms du type `100023.seq`, `453162.seq`, etc.

✅ Solution :
- création d’une version renumérotée du dataset via **liens symboliques** :
`netmob_nf_dl_small_renum/train/1.seq → original/67.seq`

---

### (3) Instabilité numérique (NaN)
Les données NetMob contiennent des valeurs pouvant dépasser 60k, ce qui provoquait :
- explosion de gradients
- `NaN` dès le premier epoch
- sorties du modèle non finies (`x_mu`, `x_logsigma`, `logits`, etc.)

✅ Solution :
- normalisation simple dans `trainer.py` :
  - `log1p`
  - standardisation (mean/std)
  - clamp des valeurs

---

### (4) Présence éventuelle de NaN dans certaines applications
Lors de l’analyse brute :
- certains fichiers (notamment Spotify) contenaient des `nan` en fin de ligne.

✅ Choix :
- priorisation du travail sur **Netflix** et **Facebook** (datasets plus stables)

---

## 4) Installation

### 1) Créer un environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate
```
### 2) Installer les dépendances
```bash
pip install -r requirements.txt
```
## 5) Prétraitement : NetMob23 → .seq

Le framework SGmVRNN attend un dataset sous forme de fichiers `.seq` PyTorch, contenant :

- `value` : tenseur `[20, 1, 96, 1]`
- `label` : tenseur `[20, 1, 1]` (étiquette au dernier timestamp)
- `ts` : tenseur `[20, 1, 1]` (timestamp)

Conversion via script :

```bash
python scripts/netmob_to_seq.py \
  --input_path "data_preprocess/Dataset NetMob23/Netflix/DL" \
  --output_path "data_preprocess/data_processed/netmob_nf_dl/train" \
  --app netflix
```
## 6) Entraînement

Exemple d’entraînement sur NetMob (small renuméroté) :
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
## 7) Résultats
Les résultats générés sont stockés ici :

📌 **Fichier score final :**

```txt
results/netmob_nf_dl_small/netmob_nf_dl_small_scores.txt
```
Format :
```txt
timestamp, score_loglikelihood, Normaly/Anomaly
```
Exemple :
```txt
42,-158.22906494140625,Normaly
54,-361.60223388671875,Normaly
```
👉 Le score correspond à la log-vraisemblance du dernier timestamp
(plus la valeur est faible/négative, plus cela indique une anomalie potentielle selon le modèle).
