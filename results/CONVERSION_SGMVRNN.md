# 🔄  Conversion NetMob23 → SGmVRNN




### Principe
```
ENTRÉE                          SORTIE
─────────────────────          ──────────────────────────
1 fichier NetMob23             77 fichiers SGmVRNN
7388 valeurs brutes      →     96 lignes × 5 colonnes chacun
(77 jours × 96 mesures)        (1 jour avec 5 features)
```

### Chiffres clés

- **Format d'entrée :** Fichier texte avec valeurs séparées par espaces
- **Format de sortie :** Tableau structuré (timestamp + 4 features)
- **Découpage temporel :** 1 fichier par jour (96 mesures de 15 minutes)
- **Features créées :** 4 features dérivées pour enrichir l'information

---


## 🔄 Les 5 étapes de conversion

### ÉTAPE 1 : Lecture du fichier NetMob23

**Code :**
```python
def read_netmob_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    date_str = lines[0].strip().split()[0]  # Ex: "20190430"
    
    all_values = []
    for line in lines:
        values = line.strip().split()
        for val in values:
            # Filtrer les dates (8 chiffres)
            if len(val) == 8 and val.isdigit():
                continue
            try:
                num_val = float(val)
                if num_val < 1000000:  # Ignorer valeurs trop grandes
                    all_values.append(num_val)
            except ValueError:
                continue
    
    return date_str, all_values
```

**Ce qui se passe :**
1. Ouvre le fichier texte
2. Lit la première ligne pour extraire la date de début
3. Parcourt toutes les lignes
4. Extrait tous les nombres (ignore les dates)
5. Retourne : date + liste de 7388 valeurs

**Résultat :**
```python
date_str = "20190430"
all_values = [1109, 1389, 1419, ..., 450]  # 7388 valeurs
```

---

### ÉTAPE 2 : Découpage par jour

**Code :**
```python
def split_into_days(date_str, values, values_per_day=96):
    n_days = len(values) // values_per_day  # 7388 // 96 = 76 jours
    days_data = []
    
    start_date = datetime.strptime(date_str, '%Y%m%d')
    
    for day_idx in range(n_days):
        start_idx = day_idx * values_per_day
        end_idx = start_idx + values_per_day
        day_values = values[start_idx:end_idx]
        
        current_date = start_date + timedelta(days=day_idx)
        
        days_data.append({
            'date': current_date,
            'values': day_values  # 96 valeurs
        })
    
    return days_data
```

**Ce qui se passe :**
1. Calcule le nombre de jours : 7388 ÷ 96 = 76 jours
2. Pour chaque jour :
   - Extrait 96 valeurs consécutives
   - Calcule la date du jour (date_début + nb_jours)
3. Retourne une liste de 76 jours

**Résultat :**
```python
days_data = [
    {'date': datetime(2019, 4, 30), 'values': [1109, 1389, ..., 895]},  # Jour 1
    {'date': datetime(2019, 5, 1),  'values': [1234, 1567, ..., 678]},  # Jour 2
    ...
    {'date': datetime(2019, 7, 14), 'values': [890, 1200, ..., 450]}   # Jour 76
]
```

---

### ÉTAPE 3 : Création des timestamps

**Code :**
```python
def create_timestamps(date, n_values=96):
    timestamps = []
    for i in range(n_values):
        timestamp = date + timedelta(minutes=15*i)
        timestamps.append(timestamp.timestamp())
    return timestamps
```

**Ce qui se passe :**
1. Pour chaque mesure (0 à 95) :
   - Ajoute 15 minutes × numéro de mesure
   - Convertit en timestamp Unix
2. Retourne 96 timestamps

**Exemple :**
```python
date = datetime(2019, 4, 30)  # 30 avril 2019, 00h00

timestamps = [
    1556582400.0,  # 30 avril 00h00
    1556583300.0,  # 30 avril 00h15
    1556584200.0,  # 30 avril 00h30
    ...
    1556668500.0   # 30 avril 23h45
]
```

**Format timestamp :**
- Nombre de secondes depuis le 1er janvier 1970 (epoch Unix)
- Format standard pour les ordinateurs
- Facile à manipuler et calculer

---

### ÉTAPE 4 : Création des features multivariées

**Code :**
```python
def create_multivariate_features(values, window=4):
    df = pd.DataFrame({'traffic': values})
    
    # Feature 2: Moyenne mobile
    df['rolling_mean'] = df['traffic'].rolling(
        window=window, 
        min_periods=1
    ).mean()
    
    # Feature 3: Écart-type mobile
    df['rolling_std'] = df['traffic'].rolling(
        window=window, 
        min_periods=1
    ).std().fillna(0)
    
    # Feature 4: Différence première
    df['diff'] = df['traffic'].diff().fillna(0)
    
    return df
```

**Ce qui se passe :**
1. Crée un DataFrame avec le trafic brut
2. Ajoute la moyenne mobile (fenêtre de 4 = 1 heure)
3. Ajoute l'écart-type mobile (fenêtre de 4)
4. Ajoute la différence première (variation)

**Résultat :**
```python
    traffic  rolling_mean  rolling_std  diff
0      1109       1109.00         0.00   0.00
1      1389       1249.00       198.00 280.00
2      1419       1305.67       165.42  30.00
3      1532       1362.25       168.50 113.00
...
```

---

### ÉTAPE 5 : Sauvegarde

**Code :**
```python
# Ajouter les timestamps en première colonne
features_df.insert(0, 'timestamp', timestamps)

# Sauvegarder au format SGmVRNN
features_df.to_csv(
    output_path, 
    sep=' ',           # Séparateur : espace
    index=False,       # Pas de numéros de ligne
    header=False,      # Pas de titres de colonnes
    float_format='%.2f'  # 2 décimales
)
```

**Format final :**
```
1556582400.00 1109.00 1109.00 0.00 0.00
1556583300.00 1389.00 1249.00 198.00 280.00
1556584200.00 1419.00 1305.67 165.42 30.00
...
```


## 📊 Les features créées

### Vue d'ensemble

| Colonne | Nom | Type | Description |
|---------|-----|------|-------------|
| 1 | `timestamp` | float | Timestamp Unix (secondes depuis 1970) |
| 2 | `traffic` | float | Valeur brute du trafic réseau |
| 3 | `rolling_mean` | float | Moyenne mobile (fenêtre = 4 mesures = 1h) |
| 4 | `rolling_std` | float | Écart-type mobile (fenêtre = 4 mesures) |
| 5 | `diff` | float | Différence première (variation) |

---

### Feature 1 : Timestamp

**Signification :** Date et heure de la mesure

**Format :** Timestamp Unix (nombre de secondes depuis le 1er janvier 1970)

**Exemple :**
```
1556582400.00 → 30 avril 2019, 00h00:00
1556583300.00 → 30 avril 2019, 00h15:00
1556584200.00 → 30 avril 2019, 00h30:00
```



---

### Feature 2 : Traffic (valeur brute)

**Signification :** Volume de trafic réseau pendant l'intervalle de 15 minutes

**Unité :** Non spécifiée dans NetMob23 (probablement MB ou nombre de requêtes)

**Exemple :**
```
Timestep 0  →  1109  (00h00-00h15)
Timestep 1  →  1389  (00h15-00h30)
Timestep 2  →  1419  (00h30-00h45)
```

**Range typique :** [0, 50000]


---

### Feature 3 : Rolling Mean (moyenne mobile)

**Signification :** Moyenne des 4 dernières valeurs (= moyenne sur 1 heure)

**Formule :**
```
rolling_mean(t) = (traffic(t-3) + traffic(t-2) + traffic(t-1) + traffic(t)) / 4
```

**Exemple concret :**
```
Timestep  Traffic  Rolling Mean (calcul)
───────────────────────────────────────────
0         1109     1109.00      (seulement 1 valeur)
1         1389     1249.00      ((1109 + 1389) / 2)
2         1419     1305.67      ((1109 + 1389 + 1419) / 3)
3         1532     1362.25      ((1109 + 1389 + 1419 + 1532) / 4)
4         1776     1529.00      ((1389 + 1419 + 1532 + 1776) / 4)
                                 └─ Fenêtre glissante de 4 valeurs
```

**Pourquoi c'est utile :**
- ✅ **Lisse les variations** : Élimine le bruit et les pics isolés
- ✅ **Montre la tendance** : Est-ce que le trafic augmente ou diminue ?
- ✅ **Contexte temporel** : Compare la valeur actuelle à la tendance récente


**Interprétation :**
```
Si traffic > rolling_mean de beaucoup → Pic anormal ⚠️
Si traffic < rolling_mean de beaucoup → Chute anormale ⚠️
Si traffic ≈ rolling_mean → Comportement normal ✅
```

---

### Feature 4 : Rolling Std (écart-type mobile)

**Signification :** Mesure de la variabilité du trafic sur la dernière heure

**Formule :**
```
rolling_std(t) = écart-type(traffic(t-3), traffic(t-2), traffic(t-1), traffic(t))
```

**Exemple concret :**
```
Situation A (stable) :
Traffic : [1000, 1010, 1005, 1015]
Moyenne : 1007.5
Écart-type : 6.45  ← FAIBLE → Stable ✅

Situation B (instable) :
Traffic : [1000, 5000, 500, 8000]
Moyenne : 3625
Écart-type : 3251.90  ← ÉLEVÉ → Instable ⚠️
```

**Pourquoi c'est utile :**
- ✅ **Détecte l'instabilité** : Identifie les comportements chaotiques
- ✅ **Mesure de confiance** : Écart-type faible = prédictions fiables
- ✅ **Indicateur d'anomalie** : Écart-type soudainement élevé = alerte


**Interprétation :**
```
rolling_std < 1000 → Trafic stable et prévisible ✅
rolling_std > 5000 → Trafic très variable, attention ⚠️
```

---

### Feature 5 : Diff (différence première)

**Signification :** Variation du trafic entre deux mesures consécutives (15 minutes d'écart)

**Formule :**
```
diff(t) = traffic(t) - traffic(t-1)
```

**Exemple concret :**
```
Timestep  Traffic  Diff (calcul)          Interprétation
──────────────────────────────────────────────────────────
0         1109     0.00    (première valeur)  Référence
1         1389     280.00  (1389 - 1109)      +280 utilisateurs
2         1419     30.00   (1419 - 1389)      +30 utilisateurs
3         1532     113.00  (1532 - 1419)      +113 utilisateurs
4         1776     244.00  (1776 - 1532)      +244 utilisateurs
```

**Pourquoi c'est utile :**
- ✅ **Détecte les sauts brusques** : Changement rapide = anomalie potentielle
- ✅ **Mesure la vitesse de changement** : Accélération ou ralentissement
- ✅ **Indépendant du niveau** : Un diff de +5000 est anormal qu'on soit à 1000 ou 10000


**Interprétation :**
```
diff ≈ 0         → Stabilité ✅
diff > +5000     → Augmentation brutale ⚠️
diff < -5000     → Chute brutale ⚠️
|diff| très élevé → Changement anormal ⚠️
```

**Exemple de scénarios :**
```
Scénario normal (fin de journée) :
23h30 → 5000
23h45 → 1000
diff = -4000  ← Normal, les gens dorment ✅

Scénario anormal (milieu de nuit) :
03h00 → 500
03h15 → 15000
diff = +14500  ← Anormal, pic suspect ! ⚠️
```

---

## 📈 Exemple complet

### Fichier d'entrée

**`Facebook_DL_Tile_92483.txt` (extrait)**
```
20190430 1109 1389 1419 1532 1776 2085 1779 777 914 979...
```

### Fichier de sortie

**`series_tile92483_day1_20190430.txt` (5 premières lignes)**
```
1556582400.00 1109.00 1109.00 0.00 0.00
1556583300.00 1389.00 1249.00 198.00 280.00
1556584200.00 1419.00 1305.67 165.42 30.00
1556585100.00 1532.00 1362.25 168.50 113.00
1556586000.00 1776.00 1529.00 252.83 244.00
```

### Explication ligne par ligne

#### Ligne 1 (00h00)
```
1556582400.00  1109.00  1109.00  0.00  0.00
│              │        │        │     │
│              │        │        │     └─ diff = 0 (première valeur)
│              │        │        └─────── rolling_std = 0 (pas assez de valeurs)
│              │        └──────────────── rolling_mean = 1109 (1 seule valeur)
│              └───────────────────────── traffic = 1109 (valeur originale)
└──────────────────────────────────────── timestamp (30 avril, 00h00)
```

#### Ligne 2 (00h15)
```
1556583300.00  1389.00  1249.00  198.00  280.00
│              │        │        │       │
│              │        │        │       └─ diff = 1389 - 1109 = 280
│              │        │        └───────── rolling_std = variation
│              │        └─────────────────── rolling_mean = (1109+1389)/2 = 1249
│              └───────────────────────────── traffic = 1389
└──────────────────────────────────────────── timestamp (30 avril, 00h15)
```

#### Ligne 5 (01h00)
```
1556586000.00  1776.00  1529.00  252.83  244.00
│              │        │        │       │
│              │        │        │       └─ diff = 1776 - 1532 = 244
│              │        │        └───────── rolling_std = ~253
│              │        └─────────────────── rolling_mean = (1389+1419+1532+1776)/4 = 1529
│              └───────────────────────────── traffic = 1776
└──────────────────────────────────────────── timestamp (30 avril, 01h00)
```

---



### Résultat 
```
======================================================================
🔄 CONVERSION NETMOB23 → SGMVRNN
======================================================================

Application: Facebook
Nombre de fichiers à convertir: 10
Dossier de sortie: ../data_converted

✓ 10 fichiers trouvés

[1/10] 📄 Traitement de Facebook_DL_Tile_92483.txt...
   • Date de début: 20190430
   • Nombre total de valeurs: 7388
   • Nombre de jours: 76
   ✓ 76 séries créées !

[2/10] ...

======================================================================
✅ CONVERSION TERMINÉE !
======================================================================

📊 Résumé:
   • Fichiers traités: 10
   • Séries créées: 760
   • Fichiers dans ../data_converted: 760
```


**Output :**
```
✓ Shape: (96, 5) (devrait être (96, 5))
✓ Traffic range: [30, 40000]
✓ NaN count: 0
📊 Graphique sauvegardé: ../results/conversion_example.png
```

---

## 📊 Statistiques de conversion

### Pour 10 fichiers Facebook

| Métrique | Valeur |
|----------|--------|
| Fichiers source | 10 |
| Valeurs par fichier source | 7388 |
| Jours par fichier | 76-77 |
| **Fichiers créés** | **760** |
| Lignes par fichier créé | 96 |
| Colonnes par fichier créé | 5 |
| **Points de données totaux** | **364 800** |

**Calcul :**
```
760 fichiers × 96 lignes × 5 colonnes = 364 800 valeurs
```

### Augmentation du nombre de fichiers

Pour convertir plus de fichiers, modifier `N_FILES` :
```python
N_FILES = 50  # 50 fichiers → 3800 séries
```

---

## 📁 Structure des fichiers générés
```
data_converted/
├── series_tile92483_day1_20190430.txt    (96 lignes × 5 colonnes)
├── series_tile92483_day2_20190501.txt
├── series_tile92483_day3_20190502.txt
├── ...
├── series_tile92483_day76_20190714.txt
├── series_tile81377_day1_20190430.txt
├── ...
└── conversion_stats.json                  (statistiques JSON)
```

**Nom du fichier :**
```
series_tile[TILE_ID]_day[JOUR]_[DATE].txt

Exemples :
- series_tile92483_day1_20190430.txt  → Zone 92483, jour 1, 30 avril 2019
- series_tile81377_day57_20190625.txt → Zone 81377, jour 57, 25 juin 2019
```

---




---

## 🔍 Validation



### Graphique de validation

![Exemple de conversion](../results/conversion_example.png)

**Interprétation :**
- **Traffic brut** : Pattern journalier typique (faible la nuit, élevé le jour)
- **Rolling mean** : Tendance lissée
- **Rolling std** : Variabilité cohérente
- **Diff** : Variations normales avec pic de fin de journée

---


---

**Dernière mise à jour :** 9 Décembre 2024  
**Auteur :** Fadwa  
**Statut :** ✅ Testé et validé
