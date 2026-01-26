#### AlertRCA – Spécialisation NetMob23

AlertRCA est un algorithme de RCA qui analyse automatiquement des alertes multimodales et construit un graphe de dépendances sans règles expertes ni traces coûteuses.  
Cette version a été spécialisée pour le dataset **NetMob23**.

**Entrée** : 
- `faults_TraceAnomaly.csv` : anomalies détectées par TraceAnomaly  
- Fichiers de trafic `.txt` par service (Facebook, Netflix), granularité 15 minutes

**Prétraitement et fichiers intermédiaires** :
- Pour chaque timestamp, **5 faults** sont sélectionnées (avec region ID et application).  
  La **region ID la plus petite** est choisie comme cause racine (`ground truth`), et elle est reliée aux 4 autres pour créer `graph.yml`.
- `faults_alertRCA.csv` : alertes converties au format AlertRCA  
- `faults.csv` : top-1 root cause par timestamp  
- `graph.yml` : graphe de dépendance des alertes (ADG)  
- `train.csv`, `valid.csv`, `test.csv` : répartition aléatoire des anomalies pour l’apprentissage  
- `metrics_filtered.csv` : métriques filtrées par nœud présent dans le graphe  
- `metrics.norm.csv` : métriques normalisées (Z-score)  
- `anomaly_direction_constraint.json` : direction des anomalies pour chaque KPI (`u`=up, `d`=down, `b`=both).  
  Dans NetMob23, les variations extrêmes de trafic (augmentation ou baisse) sont toutes considérées comme anormales, donc `b` (both).

**Sortie** : 
- `AlertRCA/A_NetMob/report_alertRCA/report_A_NetMob.json`  
  Résultat final de l’analyse RCA (classement des causes racines).  
  Pour chaque timestamp UNIX, le fichier contient :
  - `gt` : cause racine réelle  
  - `fullResponse` : classement des nœuds candidats avec leur score et label

#### Configuration
Le comportement d’AlertRCA peut être configuré via le fichier :  
`AlertRCA/graph/deep_rule.py`

#### Guide d’utilisation

Le framework AlertRCA a été modifié pour optimiser la mémoire et supporter les dernières versions des librairies.  
Pour utiliser un nouveau dataset, quelques points doivent être pris en compte :

1. **Paramètre `granularity` dans `feature_metrics`**  
   - Fichier : `AlertRCA/dejavu_dataloader/dataset.py`  
   - Classe : `feature_metrics`  
   - Le paramètre `granularity` doit correspondre à l’intervalle entre deux métriques consécutives.  
     Exemple : dans NetMob23, les métriques sont espacées de 15 minutes, donc `granularity = 60*15`.

2. **Paramètre `window_size` dans `graph_dataset`**  
   - Fichier : `AlertRCA/dejavu_dataloader/dataset.py`  
   - Classe : `graph_dataset`  
   - `window_size` définit combien de valeurs de métriques sont prises avant et après chaque fault.  
     Exemple : pour NetMob23, avec `granularity = 15 minutes`, `window_size` peut être défini pour capturer 10 valeurs avant et après, soit 150 minutes autour de chaque fault.

3. **Paramètres `start_ts` et `end_ts` dans `graph_dataset`**  
   - Initialement, ces valeurs étaient calculées avec un décalage de ±20*granularity autour des timestamps des faults.  
   - Si les métriques ne couvrent pas ces timestamps, cela peut provoquer des erreurs.  
   - Dans NetMob23, ces valeurs ont été ajustées pour correspondre exactement aux timestamps des faults :  
     ```python
     start_ts = min(failures.timestamp)
     end_ts = max(failures.timestamp)
     ```  
   - Il est conseillé de conserver cette logique ou d’ajuster en comprenant bien le mécanisme du framework.

Ces ajustements permettent au framework de traiter correctement les données et de capturer le contexte temporel pertinent autour de chaque anomalie.
