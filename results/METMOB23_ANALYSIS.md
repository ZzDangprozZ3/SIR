# 📊 Analyse du Dataset NetMob23

**Date:** 8 Décembre 2024  
**Framework assigné:** SGmVRNN

---

## 🗂️ Structure du Dataset

### Vue d'ensemble
Le dataset NetMob23 contient des données de trafic réseau mobile pour 3 applications :

| Application | Nombre de fichiers | Taille estimée | Dossier |
|-------------|-------------------|----------------|---------|
| **Facebook** | 2 565 | ~500 MB | `/Facebook/DL/` |
| **Netflix** | 54 013 | 2.0 GB | `/Netflix/DL/` |
| **Spotify** | 54 013 | 1.4 GB | `/Spotify/DL/` |

**Total:** ~110 591 fichiers, ~3.9 GB

---

## 📝 Format des Fichiers

### Structure d'un fichier `.txt`

**Exemple : `Facebook_DL_Tile_92483.txt`**
```
20190430 1109 1389 1419 1532 1776 2085 ...    ← Ligne 1 : Date + données
895 1555 1828 1444 1402 606 570 921 ...       ← Lignes suivantes
...
(7372 valeurs au total)
```

### Détails importants

- **1ère ligne:** Date de début au format `YYYYMMDD` suivie des premières valeurs
- **Total par fichier:** **7372 valeurs numériques** = **~77 jours consécutifs**
  - Chaque jour = 96 mesures (une toutes les 15 minutes)
  - Calcul: 7372 ÷ 96 ≈ 76.8 jours ≈ **2,5 mois de données**
- **Période couverte:** Du 30 avril 2019 au 31 mai 2019 (environ)
- **Granularité temporelle:** 15 minutes
  - Valeur 0 = 00h00-00h15
  - Valeur 95 = 23h45-00h00
  - Puis recommence pour le jour suivant

### Signification des valeurs

- **Type:** Volume de trafic réseau mobile (en octets ou paquets)
- **Représentation:** Chaque valeur = volume de données transférées pendant un intervalle de 15 minutes
- **Format:** Valeurs entières positives
- **Tile:** Chaque fichier correspond à une zone géographique unique (identifiée par le numéro de Tile)

---

## 📈 Statistiques Descriptives

### Résultats de l'exploration (10 fichiers par application)

#### 📱 Facebook
- **Fichiers analysés:** 10 sur 2 565
- **Valeurs par fichier:** 7 372 (= 77 jours × 96 mesures)
- **Moyenne globale:** 216 200.19
- **Maximum global:** 20 190 531.00
- **Période:** Du 30/04/2019 au 31/05/2019

**Observations:**
- Trafic moyen : ~216k unités
- Pics importants visibles (max > 20M)
- Variabilité élevée entre les zones géographiques

#### 📺 Netflix
- **Fichiers analysés:** 10 sur 54 013
- **Valeurs par fichier:** 7 372 (= 77 jours × 96 mesures)
- **Moyenne globale:** 220 611.90
- **Maximum global:** 20 190 531.00
- **Période:** Du 30/04/2019 au 31/05/2019

**Observations:**
- Trafic légèrement supérieur à Facebook (~220k)
- Beaucoup plus de fichiers (zones) que Facebook (×21)
- Pics très importants (streaming vidéo)
- Exemples de valeurs extrêmes : 257 243, 155 635

#### 🎵 Spotify
- **Fichiers analysés:** 10 sur 54 013
- **Valeurs par fichier:** 7 372 (= 77 jours × 96 mesures)
- **Moyenne globale:** 208 920.94
- **Maximum global:** 20 190 531.00
- **Période:** Du 30/04/2019 au 31/05/2019

**Observations:**
- Trafic le plus faible des trois applications (~209k)
- Streaming audio = moins de bande passante que vidéo
- Même nombre de zones que Netflix (54 013)
- Valeurs généralement plus basses (beaucoup de valeurs < 100)

### 📊 Comparaison des trois applications

| Métrique | Facebook | Netflix | Spotify |
|----------|----------|---------|---------|
| **Nombre de zones** | 2 565 | 54 013 | 54 013 |
| **Trafic moyen** | 216 200 | 220 612 | 208 921 |
| **Max observé** | 20 190 531 | 20 190 531 | 20 190 531 |
| **Type de contenu** | Social media | Streaming vidéo | Streaming audio |
| **Consommation** | Moyenne-élevée | Élevée | Moyenne |

---

## 🔄 Comparaison avec SGmVRNN Original

| Aspect | SGmVRNN Original | NetMob23 |
|--------|------------------|----------|
| **Nombre de fichiers** | 28 | 110 591 |
| **Nombre total de timesteps** | ~10 000 - 50 000 par série | 7 372 par série |
| **Format première ligne** | Timestamp Unix + features | Date YYYYMMDD + valeurs |
| **Features par timestep** | Multiples KPIs (5-10 colonnes) | 1 seul KPI (trafic réseau) |
| **Type de données** | Métriques système/réseau | Trafic mobile par application |
| **Périodicité** | Variable | Fixe : 15 minutes |
| **Durée par série** | Variable | Fixe : ~77 jours |
| **Objectif détection** | Anomalies système | Patterns de trafic mobile |

### ⚠️ Défis principaux identifiés

1. **Volume massif de données**
   - 110k fichiers vs 28 → Sous-échantillonnage obligatoire
   - Temps d'entraînement prohibitif si tous les fichiers

2. **Format différent**
   - Date au lieu de timestamp → Conversion nécessaire
   - Données sur une seule ligne au lieu de structure tabulaire

3. **Features univariées**
   - 1 seul KPI (trafic) au lieu de multiples features
   - → Nécessité de créer des features dérivées (moyennes mobiles, etc.)

4. **Données séquentielles longues**
   - 7372 timesteps par fichier
   - → Possibilité de découper en jours ou semaines

---

## 🎯 Stratégie d'Adaptation pour SGmVRNN

### 1. Sélection de données

**Proposition : Facebook uniquement** ✅
- **Pourquoi ?**
  - Plus petit dataset (2 565 fichiers vs 54 013)
  - Temps de traitement raisonnable
  - Représentatif des patterns de trafic mobile

**Sous-échantillonnage :**
- Sélectionner **50-100 zones (tiles)** aléatoirement
- Cela représente ~370k timesteps (50 × 7372)
- Temps d'entraînement estimé : ~2-4 heures (au lieu de plusieurs jours)

### 2. Conversion de format

**Transformation NetMob23 → SGmVRNN :**
```python
# Format NetMob23 (1 ligne)
20190430 1109 1389 1419 1532 ...

# Format SGmVRNN attendu (plusieurs lignes)
1556582400.0  1109  1109.5  8.2   0
1556583300.0  1389  1249.0  12.4  280
1556584200.0  1419  1305.7  10.1  30
...

# Colonnes :
# [timestamp, traffic, rolling_mean, rolling_std, diff]
```

**Features multivariées à créer :**
1. `traffic` : Valeur brute
2. `rolling_mean` : Moyenne mobile (fenêtre = 4 = 1h)
3. `rolling_std` : Écart-type mobile (fenêtre = 4)
4. `diff` : Différence première (variation)

### 3. Gestion de la temporalité

**Option A : Garder les 77 jours d'un coup**
- Avantage : Contexte temporel complet
- Inconvénient : Très long (7372 timesteps)

**Option B : Découper par jour** ✅ (Recommandé)
- Créer 77 séries de 96 timesteps à partir de chaque fichier
- Permet de multiplier les exemples d'entraînement
- 50 fichiers → 50 × 77 = 3850 séries de 96 timesteps

**Option C : Découper par semaine**
- Séries de 7 × 96 = 672 timesteps
- Compromis entre contexte et longueur

### 4. Normalisation

- **Min-Max Scaling** : Ramener les valeurs entre [0, 1]
- Calculer min/max sur l'ensemble du dataset d'entraînement
- Appliquer la même transformation sur validation/test

---

## 📋 Plan d'Action - Phase 2 (Semaine prochaine)

### Étape 2.1 : Script de conversion ✅
```bash
python scripts/convert_netmob_to_sgmvrnn.py
```
**Objectif :**
- Lire 50 fichiers Facebook aléatoires
- Convertir au format SGmVRNN (timestamp + features)
- Option de découpage par jour (77 jours → 77 séries)
- Sauvegarder dans `data_converted/`

### Étape 2.2 : Vérification ✅
```bash
python scripts/verify_conversion.py
```
**Vérifier :**
- Shape correct : (n_timesteps, n_features)
- Pas de valeurs manquantes (NaN)
- Timestamps chronologiques

### Étape 2.3 : Adapter SGmVRNN ✅
- Cloner le repo SGmVRNN original
- Créer `train_netmob.py`
- Ajuster hyperparamètres :
  - `epochs = 10` (au lieu de 100)
  - `batch_size = 64` (au lieu de 16)
  - `learning_rate = 0.001`

---

## 📊 Fichiers Générés

- ✅ `results/exploration_results.json` - Statistiques détaillées (JSON)
- ✅ `results/example_plot.png` - Visualisation d'un fichier exemple
- ✅ `scripts/explore_netmob.py` - Script d'exploration automatique
- ✅ `scripts/visualize_netmob.py` - Script de visualisation
- 🔜 `scripts/convert_netmob_to_sgmvrnn.py` - Conversion de format
- 🔜 `data_converted/` - Données converties au format SGmVRNN

---

## 💡 Observations et Remarques

### Points positifs ✅
- Dataset bien structuré et consistant
- Toutes les séries ont exactement 7372 valeurs
- Période temporelle identique pour les 3 applications
- Données réelles de réseau mobile (cas d'usage pertinent)

### Points d'attention ⚠️
- Valeurs maximales très élevées (>20M) → possibles outliers
- Nécessité de normalisation forte
- Beaucoup de petites valeurs (0-100) dans Spotify
- Le "Max global" de 20190531 semble être une date mal parsée

### Questions en suspens ❓
- Unité exacte des valeurs de trafic ? (octets, paquets, requêtes ?)
- Pourquoi certaines valeurs sont-elles égales à la date (20190531) ?
- Y a-t-il des labels d'anomalies dans le dataset ?

---

## 🔗 Ressources

- **Dataset source:** [NetMob 2023 Challenge](https://netmob2023challenge.networks.imdea.org)
- **Framework SGmVRNN:** [Lien GitHub à ajouter]
- **Projet GitHub:** [https://github.com/ZzDangprozZ3/SIR](https://github.com/ZzDangprozZ3/SIR)

---

**Dernière mise à jour:** 8 Décembre 2024  
**Statut:** Phase 1 terminée ✅ | Phase 2 en cours 🔄
