"""
================================================================================
VALIDATION CROISÉE - COMPARAISON DES MÉTHODES DE DÉTECTION
================================================================================

Ce script compare 5 méthodes de détection d'anomalies sur NetMob23 :
1. Isolation Forest seul
2. Z-Score seul
3. IQR seul
4. Vote Majoritaire (baseline)
5. AOC-IDS (prédictions du modèle entraîné)

USAGE:
    python validate_methods.py --data_path ./output/Netflix/NetflixTest.csv \\
                               --aoc_predictions ./anomalies_detected_all.csv \\
                               --service Netflix

OUTPUTS:
    - Tableaux comparatifs
    - Taux d'accord entre méthodes
    - Matrice de concordance
    - Rapport détaillé

================================================================================
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import argparse
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
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
# MÉTHODE 1 : ISOLATION FOREST
# =============================================================================

def detect_isolation_forest(df, contamination=0.1):
    """
    Détecte les anomalies avec Isolation Forest.
    
    Args:
        df: DataFrame avec les features
        contamination: Proportion d'anomalies attendue
    
    Returns:
        np.array: Labels (0=normal, 1=anomalie)
    """
    print("   [1/5] Isolation Forest...")
    
    X = df[FEATURE_NAMES].values
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    iso_forest = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100
    )
    
    predictions = iso_forest.fit_predict(X_scaled)
    labels = (predictions == -1).astype(int)
    
    print(f"       -> {np.sum(labels)} anomalies détectées ({100*np.sum(labels)/len(df):.2f}%)")
    
    return labels


# =============================================================================
# MÉTHODE 2 : Z-SCORE
# =============================================================================

def detect_zscore(df, threshold=3):
    """
    Détecte les anomalies avec Z-Score.
    
    Args:
        df: DataFrame avec les features
        threshold: Seuil Z-Score (défaut: 3)
    
    Returns:
        np.array: Labels (0=normal, 1=anomalie)
    """
    print("   [2/5] Z-Score...")
    
    labels = np.zeros(len(df))
    
    # Features clés pour Z-Score
    key_features = ['mean', 'std', 'max', 'night_mean', 'max_diff', 'volatility']
    
    for col in key_features:
        if col in df.columns:
            z_scores = np.abs(stats.zscore(df[col].fillna(0)))
            labels += (z_scores > threshold).astype(int)
    
    # Au moins une feature anormale
    labels = (labels > 0).astype(int)
    
    print(f"       -> {np.sum(labels)} anomalies détectées ({100*np.sum(labels)/len(df):.2f}%)")
    
    return labels


# =============================================================================
# MÉTHODE 3 : IQR (INTERQUARTILE RANGE)
# =============================================================================

def detect_iqr(df, multiplier=1.5):
    """
    Détecte les anomalies avec IQR (méthode des quartiles).
    
    Args:
        df: DataFrame avec les features
        multiplier: Multiplicateur IQR (défaut: 1.5)
    
    Returns:
        np.array: Labels (0=normal, 1=anomalie)
    """
    print("   [3/5] IQR (Interquartile Range)...")
    
    labels = np.zeros(len(df))
    
    # Features pour IQR
    key_features = ['mean', 'max', 'volatility', 'peak_value']
    
    for col in key_features:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - multiplier * IQR
            upper_bound = Q3 + multiplier * IQR
            
            outliers = (df[col] < lower_bound) | (df[col] > upper_bound)
            labels += outliers.astype(int)
    
    # Au moins une feature anormale
    labels = (labels > 0).astype(int)
    
    print(f"       -> {np.sum(labels)} anomalies détectées ({100*np.sum(labels)/len(df):.2f}%)")
    
    return labels


# =============================================================================
# MÉTHODE 4 : VOTE MAJORITAIRE
# =============================================================================

def detect_vote_majoritaire(df, contamination=0.1):
    """
    Détecte les anomalies par vote majoritaire (≥2/3).
    
    Args:
        df: DataFrame avec les features
        contamination: Proportion d'anomalies pour Isolation Forest
    
    Returns:
        tuple: (labels, labels_if, labels_z, labels_iqr)
    """
    print("   [4/5] Vote Majoritaire...")
    
    # Obtenir les 3 méthodes individuelles
    labels_if = detect_isolation_forest(df, contamination)
    labels_z = detect_zscore(df)
    labels_iqr = detect_iqr(df)
    
    # Vote majoritaire (≥2/3)
    combined = labels_if + labels_z + labels_iqr
    labels_vote = (combined >= 2).astype(int)
    
    print(f"   [VOTE] Vote Majoritaire...")
    print(f"       -> {np.sum(labels_vote)} anomalies détectées ({100*np.sum(labels_vote)/len(df):.2f}%)")
    
    return labels_vote, labels_if, labels_z, labels_iqr


# =============================================================================
# MÉTHODE 5 : CHARGER LES PRÉDICTIONS AOC-IDS
# =============================================================================

def load_aoc_predictions(aoc_path, df):
    """
    Charge les prédictions d'AOC-IDS depuis le fichier de résultats.
    
    Args:
        aoc_path: Chemin vers le fichier des prédictions AOC-IDS
        df: DataFrame original (pour l'alignement)
    
    Returns:
        np.array: Labels AOC-IDS (0=normal, 1=anomalie)
    """
    print("   [5/5] AOC-IDS (prédictions chargées)...")
    
    if not os.path.exists(aoc_path):
        print(f"       [ERREUR] Fichier non trouvé: {aoc_path}")
        print(f"       -> AOC-IDS sera ignoré dans la comparaison")
        return None
    
    try:
        aoc_df = pd.read_csv(aoc_path)
        
        # Vérifier que les colonnes nécessaires existent
        if 'label_predit' not in aoc_df.columns:
            print(f"       [ERREUR] Colonne 'label_predit' manquante")
            return None
        
        # Aligner avec le DataFrame original (par tile_id et date)
        if 'tile_id' in df.columns and 'date' in df.columns:
            merged = df.merge(
                aoc_df[['tile_id', 'date', 'label_predit']], 
                on=['tile_id', 'date'], 
                how='left'
            )
            labels_aoc = merged['label_predit'].fillna(0).astype(int).values
        else:
            # Si pas de métadonnées, on suppose l'ordre est le même
            labels_aoc = aoc_df['label_predit'].values[:len(df)]
        
        print(f"       -> {np.sum(labels_aoc)} anomalies détectées ({100*np.sum(labels_aoc)/len(df):.2f}%)")
        
        return labels_aoc
        
    except Exception as e:
        print(f"       [ERREUR] Impossible de charger AOC-IDS: {e}")
        return None


# =============================================================================
# CALCUL DES MÉTRIQUES DE COMPARAISON
# =============================================================================

def calculate_agreement(labels1, labels2):
    """
    Calcule le taux d'accord entre deux méthodes.
    
    Args:
        labels1: Labels méthode 1
        labels2: Labels méthode 2
    
    Returns:
        float: Taux d'accord (0-1)
    """
    return np.mean(labels1 == labels2)


def calculate_overlap(labels1, labels2):
    """
    Calcule le nombre d'anomalies communes.
    
    Args:
        labels1: Labels méthode 1
        labels2: Labels méthode 2
    
    Returns:
        int: Nombre d'anomalies détectées par les deux méthodes
    """
    return np.sum((labels1 == 1) & (labels2 == 1))


# =============================================================================
# GÉNÉRATION DU RAPPORT
# =============================================================================

def generate_report(df, labels_dict, service, output_path=None):
    """
    Génère un rapport complet de validation croisée.
    
    Args:
        df: DataFrame original
        labels_dict: Dictionnaire {nom_méthode: labels}
        service: Nom du service (Facebook/Netflix)
        output_path: Chemin pour sauvegarder le rapport
    """
    
    print("\n" + "=" * 80)
    print(f"RAPPORT DE VALIDATION CROISÉE - {service.upper()}")
    print("=" * 80)
    
    # ========== SECTION 1 : DISTRIBUTION DES ANOMALIES ==========
    print("\n1. DISTRIBUTION DES ANOMALIES DÉTECTÉES")
    print("-" * 80)
    
    total = len(df)
    
    # Baseline = Vote Majoritaire
    vote_count = np.sum(labels_dict['Vote Majoritaire'])
    
    table_data = []
    for method_name, labels in labels_dict.items():
        count = np.sum(labels)
        percentage = 100 * count / total
        diff_vs_vote = percentage - (100 * vote_count / total)
        
        table_data.append({
            'Méthode': method_name,
            'Anomalies': count,
            '% Dataset': f"{percentage:.2f}%",
            'Diff vs Vote': f"{diff_vs_vote:+.2f}%"
        })
    
    report_df = pd.DataFrame(table_data)
    print(report_df.to_string(index=False))
    
    # ========== SECTION 2 : TAUX D'ACCORD AVEC LE VOTE ==========
    print("\n2. TAUX D'ACCORD AVEC LE VOTE MAJORITAIRE")
    print("-" * 80)
    
    vote_labels = labels_dict['Vote Majoritaire']
    
    for method_name, labels in labels_dict.items():
        if method_name != 'Vote Majoritaire':
            agreement = calculate_agreement(labels, vote_labels)
            print(f"{method_name:20s} : {agreement*100:.2f}% d'accord")
    
    # ========== SECTION 3 : MATRICE DE CONCORDANCE ==========
    print("\n3. MATRICE DE CONCORDANCE (anomalies communes)")
    print("-" * 80)
    
    methods = list(labels_dict.keys())
    n_methods = len(methods)
    
    # En-tête
    print(f"{'':15s}", end='')
    for method in methods:
        print(f"{method[:12]:>12s}", end='')
    print()
    
    # Matrice
    for i, method1 in enumerate(methods):
        print(f"{method1[:15]:15s}", end='')
        for j, method2 in enumerate(methods):
            if i == j:
                # Diagonale : nombre total d'anomalies
                count = np.sum(labels_dict[method1])
            else:
                # Hors diagonale : anomalies communes
                count = calculate_overlap(labels_dict[method1], labels_dict[method2])
            
            print(f"{count:12d}", end='')
        print()
    
    # ========== SECTION 4 : ANALYSE QUALITATIVE ==========
    print("\n4. ANALYSE QUALITATIVE")
    print("-" * 80)
    
    # Anomalies détectées par TOUTES les méthodes (consensus fort)
    all_methods_labels = np.ones(len(df))
    for labels in labels_dict.values():
        all_methods_labels = all_methods_labels * labels
    
    consensus_count = np.sum(all_methods_labels)
    print(f"Anomalies détectées par TOUTES les méthodes : {consensus_count} ({100*consensus_count/total:.2f}%)")
    
    # Anomalies détectées par au moins UNE méthode
    any_method_labels = np.zeros(len(df))
    for labels in labels_dict.values():
        any_method_labels = np.maximum(any_method_labels, labels)
    
    any_count = np.sum(any_method_labels)
    print(f"Anomalies détectées par AU MOINS une méthode : {any_count} ({100*any_count/total:.2f}%)")
    
    # Anomalies uniques à AOC-IDS (si disponible)
    if 'AOC-IDS' in labels_dict:
        aoc_labels = labels_dict['AOC-IDS']
        vote_labels = labels_dict['Vote Majoritaire']
        
        aoc_only = np.sum((aoc_labels == 1) & (vote_labels == 0))
        vote_only = np.sum((aoc_labels == 0) & (vote_labels == 1))
        
        print(f"\nAnomaliesdétectées UNIQUEMENT par AOC-IDS : {aoc_only}")
        print(f"Anomalies détectées UNIQUEMENT par Vote : {vote_only}")
    
    # ========== SECTION 5 : CONCLUSION ==========
    print("\n5. CONCLUSION")
    print("-" * 80)
    
    if 'AOC-IDS' in labels_dict:
        aoc_agreement = calculate_agreement(labels_dict['AOC-IDS'], vote_labels)
        print(f"✓ AOC-IDS a un taux d'accord de {aoc_agreement*100:.2f}% avec le vote majoritaire")
        
        aoc_count = np.sum(labels_dict['AOC-IDS'])
        vote_count = np.sum(vote_labels)
        diff_percent = 100 * abs(aoc_count - vote_count) / vote_count
        print(f"✓ AOC-IDS détecte {aoc_count} anomalies vs {vote_count} pour le vote ({diff_percent:.1f}% de différence)")
        
        if aoc_agreement > 0.90:
            print("✓ EXCELLENT : AOC-IDS est très cohérent avec le vote majoritaire")
        elif aoc_agreement > 0.80:
            print("✓ BON : AOC-IDS est cohérent avec le vote majoritaire")
        else:
            print("⚠ ATTENTION : AOC-IDS diverge du vote majoritaire")
    
    print("\n" + "=" * 80)
    
    # ========== SAUVEGARDE DU RAPPORT ==========
    if output_path:
        # Créer un rapport texte
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"RAPPORT DE VALIDATION CROISÉE - {service.upper()}")
        report_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("\n" + report_df.to_string(index=False))
        
        with open(output_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"\n[SAVE] Rapport sauvegardé: {output_path}")


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def main():
    """Point d'entrée du script."""
    
    parser = argparse.ArgumentParser(
        description='Validation croisée des méthodes de détection d\'anomalies'
    )
    
    parser.add_argument('--data_path', type=str, required=True,
                        help='Chemin vers le fichier CSV de données (ex: NetflixTest.csv)')
    parser.add_argument('--aoc_predictions', type=str, default=None,
                        help='Chemin vers les prédictions AOC-IDS (ex: anomalies_detected_all.csv)')
    parser.add_argument('--service', type=str, required=True,
                        help='Nom du service (Facebook ou Netflix)')
    parser.add_argument('--contamination', type=float, default=0.1,
                        help='Proportion d\'anomalies pour Isolation Forest (défaut: 0.1)')
    parser.add_argument('--output_report', type=str, default=None,
                        help='Chemin pour sauvegarder le rapport (optionnel)')
    
    args = parser.parse_args()
    
    # ========== CHARGEMENT DES DONNÉES ==========
    print("\n" + "=" * 80)
    print("VALIDATION CROISÉE - CHARGEMENT DES DONNÉES")
    print("=" * 80)
    
    if not os.path.exists(args.data_path):
        print(f"[ERREUR] Fichier non trouvé: {args.data_path}")
        return
    
    print(f"[INFO] Chargement: {args.data_path}")
    df = pd.read_csv(args.data_path)
    
    print(f"[INFO] Dataset chargé: {len(df)} lignes")
    
    # Vérifier les features
    missing_features = [f for f in FEATURE_NAMES if f not in df.columns]
    if missing_features:
        print(f"[ERREUR] Features manquantes: {missing_features}")
        return
    
    # ========== APPLICATION DES MÉTHODES ==========
    print("\n" + "=" * 80)
    print("APPLICATION DES MÉTHODES DE DÉTECTION")
    print("=" * 80)
    
    labels_dict = {}
    
    # Méthode 4 : Vote Majoritaire (qui appelle les 3 premières)
    labels_vote, labels_if, labels_z, labels_iqr = detect_vote_majoritaire(df, args.contamination)
    
    labels_dict['Isolation Forest'] = labels_if
    labels_dict['Z-Score'] = labels_z
    labels_dict['IQR'] = labels_iqr
    labels_dict['Vote Majoritaire'] = labels_vote
    
    # Méthode 5 : AOC-IDS (optionnel)
    if args.aoc_predictions:
        labels_aoc = load_aoc_predictions(args.aoc_predictions, df)
        if labels_aoc is not None:
            labels_dict['AOC-IDS'] = labels_aoc
    
    # ========== GÉNÉRATION DU RAPPORT ==========
    generate_report(df, labels_dict, args.service, args.output_report)
    
    print("\n[OK] Validation terminée!")

if __name__ == "__main__":
    main()