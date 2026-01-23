"""
================================================================================
NETMOB23 -> AOC-IDS CONVERTER (VERSION SEPAREE FACEBOOK/NETFLIX)
VERSION MODIFIEE : Détection INTELLIGENTE de la colonne 'label'
================================================================================

Ce script convertit les donnees NetMob23 (series temporelles de trafic mobile)
en format compatible avec le framework AOC-IDS (detection d'anomalies).

MODIFICATION INTELLIGENTE:
    - Détection par NOM: cherche 'label', 'labels', 'anomaly', 'class', 'target', etc.
    - Détection par CONTENU: cherche toute colonne binaire (0/1)
    - Si labels trouvés, ils sont conservés (pas de vote majoritaire)
    - Si pas de labels, vote majoritaire est appliqué automatiquement

STRUCTURE D'ENTREE:
    NetMob23/
    |-- Facebook/
    |   +-- DL/
    |       |-- Facebook_DL_Tile_120022.txt
    |       +-- ...
    +-- Netflix/
        +-- DL/
            |-- Netflix_DL_Tile_120022.txt
            +-- ...

STRUCTURE DE SORTIE:
    output/
    |-- Facebook/
    |   |-- FacebookTrain.csv  (70%)
    |   +-- FacebookTest.csv   (30%)
    +-- Netflix/
        |-- NetflixTrain.csv   (70%)
        +-- NetflixTest.csv    (30%)

FEATURES (15):
    - mean, std, min, max (statistiques)
    - skewness (forme)
    - night_mean, morning_mean, day_night_ratio (temporelles)
    - peak_value, peak_hour (pics)
    - max_diff, volatility (variation)
    - entropy, trend_slope (complexite)
    - peak_to_mean (energie)

================================================================================
"""

# =============================================================================
# SECTION 1 : IMPORTATION DES BIBLIOTHEQUES
# =============================================================================

import os
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import warnings
import argparse

warnings.filterwarnings('ignore')


# =============================================================================
# SECTION 2 : CONFIGURATION DES 15 FEATURES
# =============================================================================

FEATURE_NAMES = [
    'mean', 'std', 'min', 'max',
    'skewness',
    'night_mean', 'morning_mean', 'day_night_ratio',
    'peak_value', 'peak_hour',
    'max_diff', 'volatility',
    'entropy', 'trend_slope',
    'peak_to_mean'
]


# =============================================================================
# SECTION 3 : PARSING D'UNE LIGNE
# =============================================================================

def parse_line(line):
    """
    Parse une ligne du fichier NetMob23.
    
    Format: "20190430 385 519 671 756 ..." (date + 96 valeurs)
    
    Returns:
        tuple: (date, numpy_array) ou (None, None) si erreur
    """
    parts = line.strip().split()
    
    if len(parts) < 10:
        return None, None
    
    date = parts[0]
    values = []
    
    for v in parts[1:]:
        try:
            val = float(v)
            if np.isnan(val):
                values.append(0.0)
            else:
                values.append(val)
        except (ValueError, TypeError):
            values.append(0.0)
    
    return date, np.array(values)


# =============================================================================
# SECTION 4 : EXTRACTION DES 15 FEATURES
# =============================================================================

def extract_features(values, date, tile_id):
    """
    Extrait les 15 features d'une serie temporelle.
    
    Args:
        values: Tableau de 96 valeurs (trafic sur 24h)
        date: Date au format YYYYMMDD
        tile_id: Identifiant de la tuile
    
    Returns:
        dict: Dictionnaire avec les 15 features + metadonnees
    """
    
    # Validation
    if len(values) == 0 or np.sum(values) == 0:
        return None
    
    if np.any(np.isnan(values)):
        values = np.nan_to_num(values, nan=np.nanmean(values))
    
    features = {}
    
    # ----- STATISTIQUES DE BASE (4) -----
    features['mean'] = np.mean(values)
    features['std'] = np.std(values)
    features['min'] = np.min(values)
    features['max'] = np.max(values)
    
    # ----- FORME (1) -----
    if features['std'] > 0:
        features['skewness'] = stats.skew(values)
    else:
        features['skewness'] = 0.0
    
    # ----- TEMPORELLES (3) -----
    n = len(values)
    
    if n >= 96:
        night = values[0:24]
        morning = values[24:48]
        afternoon = values[48:72]
        evening = values[72:96]
    else:
        quarter = n // 4
        night = values[0:quarter]
        morning = values[quarter:2*quarter]
        afternoon = values[2*quarter:3*quarter]
        evening = values[3*quarter:]
    
    features['night_mean'] = np.mean(night) if len(night) > 0 else 0.0
    features['morning_mean'] = np.mean(morning) if len(morning) > 0 else 0.0
    
    afternoon_mean = np.mean(afternoon) if len(afternoon) > 0 else 0.0
    evening_mean = np.mean(evening) if len(evening) > 0 else 0.0
    
    day_traffic = features['morning_mean'] + afternoon_mean
    night_traffic = features['night_mean'] + evening_mean
    
    if night_traffic > 0:
        features['day_night_ratio'] = day_traffic / night_traffic
    else:
        features['day_night_ratio'] = 0.0
    
    # ----- PICS (2) -----
    features['peak_value'] = features['max']
    peak_index = np.argmax(values)
    features['peak_hour'] = peak_index * (24.0 / n)
    
    # ----- VARIATION (2) -----
    diff = np.diff(values)
    features['max_diff'] = np.max(np.abs(diff))
    
    signs = np.sign(diff)
    sign_changes = np.diff(signs)
    features['volatility'] = np.sum(sign_changes != 0)
    
    # ----- COMPLEXITE (2) -----
    hist, _ = np.histogram(values, bins=10, density=True)
    hist = hist[hist > 0]
    if len(hist) > 0:
        features['entropy'] = -np.sum(hist * np.log(hist))
    else:
        features['entropy'] = 0.0
    
    x = np.arange(len(values))
    if len(values) > 1:
        slope, _, _, _, _ = stats.linregress(x, values)
        features['trend_slope'] = slope
    else:
        features['trend_slope'] = 0.0
    
    # ----- ENERGIE (1) -----
    if features['mean'] > 0:
        features['peak_to_mean'] = features['peak_value'] / features['mean']
    else:
        features['peak_to_mean'] = 0.0
    
    # ----- METADONNEES -----
    features['tile_id'] = tile_id
    features['date'] = date
    
    return features


# =============================================================================
# SECTION 5 : TRAITEMENT D'UN FICHIER
# =============================================================================

def process_file(filepath, tile_id):
    """
    Traite un fichier de tuile NetMob23.
    
    Args:
        filepath: Chemin vers le fichier .txt
        tile_id: ID de la tuile
    
    Returns:
        list: Liste de dictionnaires (un par jour)
    """
    records = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                date, values = parse_line(line)
                
                if date is not None and values is not None:
                    features = extract_features(values, date, tile_id)
                    
                    if features is not None:
                        records.append(features)
    except Exception as e:
        print(f"[ERREUR] Impossible de lire {filepath}: {e}")
    
    return records


# =============================================================================
# SECTION 6 : TRAITEMENT D'UN SERVICE (Facebook ou Netflix)
# =============================================================================

def process_service(base_path, service):
    """
    Traite tous les fichiers d'un service (Facebook ou Netflix).
    
    Args:
        base_path: Chemin racine NetMob23
        service: 'Facebook' ou 'Netflix'
    
    Returns:
        pd.DataFrame: DataFrame avec toutes les donnees du service
    """
    all_records = []
    
    dl_path = os.path.join(base_path, service, 'DL')
    
    if not os.path.exists(dl_path):
        print(f"[ERREUR] Dossier non trouve: {dl_path}")
        return pd.DataFrame()
    
    files = [f for f in os.listdir(dl_path) if f.endswith('.txt')]
    total_files = len(files)
    
    print(f"\n[INFO] Traitement de {service}/DL/")
    print(f"       {total_files} fichiers a traiter")
    
    for i, filename in enumerate(files):
        filepath = os.path.join(dl_path, filename)
        
        # Extraire tile_id du nom de fichier
        tile_id = filename.replace(f'{service}_DL_Tile_', '').replace('.txt', '')
        
        records = process_file(filepath, tile_id)
        all_records.extend(records)
        
        # Progression tous les 100 fichiers ou a la fin
        if (i + 1) % 100 == 0 or (i + 1) == total_files:
            print(f"       -> {i+1}/{total_files} fichiers ({len(all_records)} enregistrements)")
    
    df = pd.DataFrame(all_records)
    print(f"[OK] {service}: {len(df)} enregistrements extraits")
    
    return df


# =============================================================================
# SECTION 7 : DETECTION D'ANOMALIES (VOTE MAJORITAIRE)
# =============================================================================

def detect_anomalies(df, contamination=0.1):
    """
    Detecte les anomalies avec 3 methodes + vote majoritaire.
    
    Args:
        df: DataFrame avec les features
        contamination: Proportion d'anomalies (0.1 = 10%)
    
    Returns:
        np.array: Labels (0=normal, 1=anomalie)
    """
    print("       Detection d'anomalies par vote majoritaire...")
    
    # Preparer les donnees
    X = df[FEATURE_NAMES].values
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Methode 1: Isolation Forest
    iso_forest = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100
    )
    iso_pred = iso_forest.fit_predict(X_scaled)
    iso_labels = (iso_pred == -1).astype(int)
    
    # Methode 2: Z-Score
    z_labels = np.zeros(len(df))
    key_features = ['mean', 'std', 'max', 'night_mean', 'max_diff', 'volatility']
    for col in key_features:
        if col in df.columns:
            z_scores = np.abs(stats.zscore(df[col].fillna(0)))
            z_labels += (z_scores > 3).astype(int)
    z_labels = (z_labels > 0).astype(int)
    
    # Methode 3: IQR
    iqr_labels = np.zeros(len(df))
    for col in ['mean', 'max', 'volatility']:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = (df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)
            iqr_labels += outliers.astype(int)
    iqr_labels = (iqr_labels > 0).astype(int)
    
    # Vote majoritaire
    combined = iso_labels + z_labels + iqr_labels
    final_labels = (combined >= 2).astype(int)
    
    print(f"       -> Isolation Forest: {np.sum(iso_labels)} anomalies")
    print(f"       -> Z-Score: {np.sum(z_labels)} anomalies")
    print(f"       -> IQR: {np.sum(iqr_labels)} anomalies")
    print(f"       -> Vote majoritaire: {np.sum(final_labels)} anomalies")
    
    return final_labels


# =============================================================================
# SECTION 8 : CREATION DES DATASETS POUR UN SERVICE
# =============================================================================

def create_service_datasets(df, service, output_dir, test_size=0.3, contamination=0.1):
    """
    Cree les fichiers Train et Test pour un service.
    
    MODIFICATION: Detecte INTELLIGEMMENT si une colonne de labels existe
    
    Args:
        df: DataFrame avec les features
        service: 'Facebook' ou 'Netflix'
        output_dir: Dossier de sortie racine
        test_size: Proportion test (0.3 = 30%)
        contamination: Proportion d'anomalies
    
    Returns:
        tuple: (train_df, test_df)
    """
    print(f"\n[INFO] Creation des datasets {service}")
    
    # ========== DETECTION INTELLIGENTE DES LABELS ==========
    # Méthode 1: Chercher par nom de colonne commun
    label_column_candidates = [
        'label', 'labels', 'Label', 'Labels', 
        'anomaly', 'Anomaly', 'anomalies', 'Anomalies',
        'is_anomaly', 'is_normal',
        'class', 'Class', 'classe', 'Classe',
        'target', 'Target', 'y', 'Y'
    ]
    
    label_column_found = None
    for candidate in label_column_candidates:
        if candidate in df.columns:
            label_column_found = candidate
            print(f"       [DETECTION PAR NOM] Colonne '{candidate}' trouvee")
            break
    
    # Méthode 2: Chercher par contenu (colonnes binaires avec uniquement 0 et 1)
    if label_column_found is None:
        print("       [DETECTION PAR NOM] Aucune colonne reconnue")
        print("       [DETECTION PAR CONTENU] Recherche d'une colonne binaire (0/1)...")
        
        for col in df.columns:
            # Ignorer les colonnes de features connues et métadonnées
            if col in FEATURE_NAMES or col in ['tile_id', 'date']:
                continue
            
            # Vérifier si la colonne contient uniquement des 0 et 1
            try:
                unique_values = df[col].dropna().unique()
                # Accepter int ou float
                unique_set = set([int(v) if not np.isnan(v) else v for v in unique_values])
                
                if len(unique_set) == 2 and unique_set.issubset({0, 1}):
                    label_column_found = col
                    print(f"       [DETECTION PAR CONTENU] Colonne binaire trouvee: '{col}'")
                    print(f"       -> Valeurs uniques: {sorted(unique_values)}")
                    break
            except:
                continue
    
    # Utiliser les labels existants ou générer par vote majoritaire
    if label_column_found is not None:
        print(f"       [OK] Utilisation de la colonne: '{label_column_found}'")
        print("       -> Les labels existants seront conserves (pas de vote majoritaire)")
        
        labels = df[label_column_found].values
        
        # Convertir en int si nécessaire
        labels = labels.astype(int)
        
        # Si la colonne n'est pas nommée 'label', la renommer
        if label_column_found != 'label':
            df['label'] = labels
            print(f"       -> Colonne '{label_column_found}' renommee en 'label'")
        else:
            df['label'] = labels
        
        # Statistiques sur les labels existants
        n_normal = np.sum(labels == 0)
        n_anomaly = np.sum(labels == 1)
        print(f"       Distribution: {n_normal} normaux ({100*n_normal/len(df):.1f}%), {n_anomaly} anomalies ({100*n_anomaly/len(df):.1f}%)")
        
    else:
        print("       [DETECTION] Aucune colonne de labels trouvee")
        print("       -> Application du vote majoritaire (3 methodes)")
        
        # Generer les labels par vote majoritaire
        labels = detect_anomalies(df, contamination)
        df['label'] = labels
        
        n_normal = np.sum(labels == 0)
        n_anomaly = np.sum(labels == 1)
        print(f"       Distribution: {n_normal} normaux ({100*n_normal/len(df):.1f}%), {n_anomaly} anomalies ({100*n_anomaly/len(df):.1f}%)")
    # ========================================================
    
    # Split 70/30
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df['label'],
        random_state=42
    )
    
    # Ordre des colonnes: features + tile_id + date + label
    columns = FEATURE_NAMES + ['tile_id', 'date', 'label']
    train_df = train_df[columns]
    test_df = test_df[columns]
    
    # Creer le dossier de sortie
    service_output_dir = os.path.join(output_dir, service)
    os.makedirs(service_output_dir, exist_ok=True)
    
    # Sauvegarder
    train_path = os.path.join(service_output_dir, f'{service}Train.csv')
    test_path = os.path.join(service_output_dir, f'{service}Test.csv')
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"[SAVE] {service}Train.csv: {len(train_df)} lignes ({np.sum(train_df['label']==1)} anomalies)")
    print(f"[SAVE] {service}Test.csv: {len(test_df)} lignes ({np.sum(test_df['label']==1)} anomalies)")
    
    return train_df, test_df


# =============================================================================
# SECTION 9 : AFFICHAGE DES FEATURES
# =============================================================================

def print_features():
    """Affiche la liste des 15 features."""
    
    print("\n" + "=" * 60)
    print("LES 15 FEATURES")
    print("=" * 60)
    
    descriptions = {
        'mean': 'Moyenne du trafic sur 24h',
        'std': 'Ecart-type (dispersion)',
        'min': 'Valeur minimale',
        'max': 'Valeur maximale (pic)',
        'skewness': 'Asymetrie de la distribution',
        'night_mean': 'Trafic moyen 00h-06h',
        'morning_mean': 'Trafic moyen 06h-12h',
        'day_night_ratio': 'Ratio jour/nuit',
        'peak_value': 'Valeur du pic',
        'peak_hour': 'Heure du pic (0-24)',
        'max_diff': 'Variation maximale',
        'volatility': 'Nombre de changements de direction',
        'entropy': 'Mesure du desordre',
        'trend_slope': 'Pente de la tendance',
        'peak_to_mean': 'Ratio pic/moyenne'
    }
    
    for i, f in enumerate(FEATURE_NAMES, 1):
        print(f"  {i:2d}. {f:20s} : {descriptions[f]}")


# =============================================================================
# SECTION 10 : FONCTION PRINCIPALE
# =============================================================================

def main():
    """Point d'entree du script."""
    
    parser = argparse.ArgumentParser(
        description='Convertit NetMob23 en format AOC-IDS - VERSION INTELLIGENTE avec detection auto de labels'
    )
    
    parser.add_argument('--input', type=str,
                        help='Chemin vers le dossier NetMob23')
    parser.add_argument('--output', type=str, default='./output',
                        help='Dossier de sortie (defaut: ./output)')
    parser.add_argument('--contamination', type=float, default=0.1,
                        help='Proportion d\'anomalies si pas de labels (defaut: 0.1 = 10%%)')
    parser.add_argument('--test_size', type=float, default=0.3,
                        help='Proportion test (defaut: 0.3 = 30%%)')
    parser.add_argument('--features', action='store_true',
                        help='Afficher la liste des features')
    
    args = parser.parse_args()
    
    # Afficher les features si demande
    if args.features:
        print_features()
        return
    
    # Verifier les arguments
    if not args.input:
        print("[ERREUR] Veuillez specifier --input /chemin/vers/NetMob23")
        return
    
    if not os.path.exists(args.input):
        print(f"[ERREUR] Chemin non trouve: {args.input}")
        return
    
    # Afficher la configuration
    print("\n" + "=" * 60)
    print("CONFIGURATION")
    print("=" * 60)
    print(f"Entree:        {args.input}")
    print(f"Sortie:        {args.output}")
    print(f"Train/Test:    {int((1-args.test_size)*100)}% / {int(args.test_size*100)}%")
    print(f"Contamination: {args.contamination*100:.0f}% (si pas de labels)")
    print(f"Features:      {len(FEATURE_NAMES)}")
    print("\n[NOUVEAU] Detection INTELLIGENTE de la colonne 'label':")
    print("          1. Recherche par NOM (label, labels, anomaly, class, target, etc.)")
    print("          2. Recherche par CONTENU (colonnes binaires 0/1)")
    print("          3. Si trouvee -> conserve les labels")
    print("          4. Si absente -> vote majoritaire (3 algos)")
    
    # Traiter chaque service separement
    services = ['Facebook', 'Netflix']
    
    print("\n" + "=" * 60)
    print("TRAITEMENT DES DONNEES")
    print("=" * 60)
    
    for service in services:
        # Extraire les features
        df = process_service(args.input, service)
        
        if len(df) == 0:
            print(f"[ATTENTION] Aucune donnee pour {service}, passage au suivant")
            continue
        
        # Creer les datasets Train/Test
        create_service_datasets(
            df, 
            service, 
            args.output, 
            test_size=args.test_size,
            contamination=args.contamination
        )
    
    # Afficher les features
    print_features()
    
    # Resume final
    print("\n" + "=" * 60)
    print("STRUCTURE DE SORTIE")
    print("=" * 60)
    print(f"{args.output}/")
    print("|-- Facebook/")
    print("|   |-- FacebookTrain.csv (70%)")
    print("|   +-- FacebookTest.csv  (30%)")
    print("+-- Netflix/")
    print("    |-- NetflixTrain.csv  (70%)")
    print("    +-- NetflixTest.csv   (30%)")
    
    print("\n" + "=" * 60)
    print("[OK] CONVERSION TERMINEE!")
    print("=" * 60)


if __name__ == "__main__":
    main()