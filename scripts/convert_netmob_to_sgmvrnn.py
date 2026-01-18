
"""
Script de conversion NetMob23 → Format SGmVRNN
Auteur: Fadwa
Date: Décembre 2024
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json

# ========================================
# CONFIGURATION
# ========================================

BASE_PATH = "/home/lenovo-loq/Bureau/Dataset NetMob23"
APP_NAME = "Facebook"  # On commence par Facebook (plus petit)

# Dossiers de sortie
OUTPUT_DIR = Path("../data_converted")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Nombre de fichiers à convertir (commence petit pour tester)
N_FILES = 10  # On teste avec 10 fichiers d'abord

# ========================================
# PARTIE 1 : LECTURE D'UN FICHIER NETMOB
# ========================================

def read_netmob_file(filepath):
    """
    Lit un fichier NetMob23
    
    Args:
        filepath: Chemin vers le fichier .txt
        
    Returns:
        tuple: (date_debut, liste_valeurs)
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Première ligne = date + premières valeurs
    first_line = lines[0].strip().split()
    date_str = first_line[0]  # Ex: "20190430"
    
    # Toutes les valeurs (première ligne + lignes suivantes)
    all_values = []
    
    for line in lines:
        values = line.strip().split()
        for val in values:
            # Ignorer les valeurs qui ressemblent à des dates (8 chiffres)
            if len(val) == 8 and val.isdigit():
                continue
            
            try:
                num_val = float(val)
                # Ignorer les valeurs trop grandes (probablement des dates)
                if num_val < 1000000:  # Seuil arbitraire
                    all_values.append(num_val)
            except ValueError:
                # Ignorer les valeurs non-numériques
                continue
    
    return date_str, all_values


# ========================================
# PARTIE 2 : DÉCOUPAGE PAR JOUR
# ========================================

def split_into_days(date_str, values, values_per_day=96):
    """
    Découpe une longue série en jours
    
    Args:
        date_str: Date de début (format YYYYMMDD)
        values: Liste de toutes les valeurs
        values_per_day: Nombre de valeurs par jour (96 = 15min × 24h)
        
    Returns:
        list: Liste de dictionnaires {date, day_values}
    """
    n_days = len(values) // values_per_day
    days_data = []
    
    # Convertir la date de début
    start_date = datetime.strptime(date_str, '%Y%m%d')
    
    for day_idx in range(n_days):
        # Extraire les valeurs du jour
        start_idx = day_idx * values_per_day
        end_idx = start_idx + values_per_day
        day_values = values[start_idx:end_idx]
        
        # Calculer la date du jour
        current_date = start_date + timedelta(days=day_idx)
        
        days_data.append({
            'date': current_date,
            'date_str': current_date.strftime('%Y%m%d'),
            'values': day_values
        })
    
    return days_data


# ========================================
# PARTIE 3 : CRÉER FEATURES MULTIVARIÉES
# ========================================

def create_multivariate_features(values, window=4):
    """
    Crée des features multivariées à partir d'une série univariée
    
    Features créées:
    1. traffic : Valeur brute
    2. rolling_mean : Moyenne mobile
    3. rolling_std : Écart-type mobile
    4. diff : Différence première
    
    Args:
        values: Liste des valeurs brutes
        window: Taille de la fenêtre pour rolling (4 = 1 heure)
        
    Returns:
        DataFrame: Tableau avec features multivariées
    """
    df = pd.DataFrame({'traffic': values})
    
    # Feature 2: Moyenne mobile
    df['rolling_mean'] = df['traffic'].rolling(window=window, min_periods=1).mean()
    
    # Feature 3: Écart-type mobile
    df['rolling_std'] = df['traffic'].rolling(window=window, min_periods=1).std().fillna(0)
    
    # Feature 4: Différence première (variation)
    df['diff'] = df['traffic'].diff().fillna(0)
    
    return df


# ========================================
# PARTIE 4 : CRÉER TIMESTAMPS
# ========================================

def create_timestamps(date, n_values=96):
    """
    Crée des timestamps pour les mesures (15 min d'intervalle)
    
    Args:
        date: Date du jour (datetime object)
        n_values: Nombre de valeurs (96 = 24h)
        
    Returns:
        list: Liste de timestamps Unix
    """
    timestamps = []
    
    for i in range(n_values):
        timestamp = date + timedelta(minutes=15*i)
        timestamps.append(timestamp.timestamp())
    
    return timestamps


# ========================================
# PARTIE 5 : CONVERSION COMPLÈTE
# ========================================

def convert_file_to_sgmvrnn_format(filepath, tile_id):
    """
    Convertit UN fichier NetMob23 en PLUSIEURS fichiers SGmVRNN
    (un fichier par jour)
    
    Args:
        filepath: Chemin vers le fichier NetMob23
        tile_id: Identifiant de la zone (Tile)
        
    Returns:
        int: Nombre de séries créées
    """
    print(f"\n📄 Traitement de {filepath.name}...")
    
    # 1. Lire le fichier
    date_str, values = read_netmob_file(filepath)
    print(f"   • Date de début: {date_str}")
    print(f"   • Nombre total de valeurs: {len(values)}")
    
    # 2. Découper en jours
    days_data = split_into_days(date_str, values)
    print(f"   • Nombre de jours: {len(days_data)}")
    
    # 3. Créer un fichier par jour
    series_created = 0
    
    for day_idx, day_data in enumerate(days_data):
        # Créer features multivariées
        features_df = create_multivariate_features(day_data['values'])
        
        # Créer timestamps
        timestamps = create_timestamps(day_data['date'])
        features_df.insert(0, 'timestamp', timestamps)
        
        # Nom du fichier de sortie
        output_filename = f"series_tile{tile_id}_day{day_idx+1}_{day_data['date_str']}.txt"
        output_path = OUTPUT_DIR / output_filename
        
        # Sauvegarder (format SGmVRNN : espace-séparé, pas de header)
        features_df.to_csv(output_path, sep=' ', index=False, header=False, float_format='%.2f')
        
        series_created += 1
    
    print(f"   ✓ {series_created} séries créées !")
    return series_created


# ========================================
# PARTIE 6 : TRAITEMENT PAR LOTS
# ========================================

def convert_multiple_files(n_files=10):
    """
    Convertit plusieurs fichiers NetMob23
    
    Args:
        n_files: Nombre de fichiers à convertir
    """
    print("\n" + "="*70)
    print(f"🔄 CONVERSION NETMOB23 → SGMVRNN")
    print("="*70)
    print(f"\nApplication: {APP_NAME}")
    print(f"Nombre de fichiers à convertir: {n_files}")
    print(f"Dossier de sortie: {OUTPUT_DIR}")
    
    # Chemin vers les fichiers
    dl_path = Path(BASE_PATH) / APP_NAME / 'DL'
    
    if not dl_path.exists():
        print(f"\n❌ ERREUR: Le dossier {dl_path} n'existe pas !")
        return
    
    # Lister les fichiers
    all_files = list(dl_path.glob('*.txt'))[:n_files]
    
    if len(all_files) == 0:
        print(f"\n❌ Aucun fichier trouvé dans {dl_path}")
        return
    
    print(f"\n✓ {len(all_files)} fichiers trouvés")
    
    # Statistiques
    total_series = 0
    conversion_stats = []
    
    # Convertir chaque fichier
    for idx, filepath in enumerate(all_files, 1):
        print(f"\n[{idx}/{len(all_files)}] ", end='')
        
        # Extraire l'ID du Tile depuis le nom du fichier
        # Ex: "Facebook_DL_Tile_92483.txt" → "92483"
        tile_id = filepath.stem.split('_')[-1]
        
        try:
            n_series = convert_file_to_sgmvrnn_format(filepath, tile_id)
            total_series += n_series
            
            conversion_stats.append({
                'filename': filepath.name,
                'tile_id': tile_id,
                'series_created': n_series
            })
            
        except Exception as e:
            print(f"   ✗ ERREUR: {e}")
    
    # Résumé
    print("\n" + "="*70)
    print("✅ CONVERSION TERMINÉE !")
    print("="*70)
    print(f"\n📊 Résumé:")
    print(f"   • Fichiers traités: {len(conversion_stats)}")
    print(f"   • Séries créées: {total_series}")
    print(f"   • Fichiers dans {OUTPUT_DIR}: {len(list(OUTPUT_DIR.glob('*.txt')))}")
    
    # Sauvegarder les stats
    stats_file = OUTPUT_DIR / "conversion_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(conversion_stats, f, indent=2)
    print(f"\n💾 Statistiques sauvegardées: {stats_file}")
    
    # Exemple de fichier créé
    example_files = list(OUTPUT_DIR.glob('*.txt'))[:3]
    if example_files:
        print(f"\n📝 Exemples de fichiers créés:")
        for f in example_files:
            print(f"   • {f.name}")


# ========================================
# POINT D'ENTRÉE
# ========================================

def main():
    """Fonction principale"""
    convert_multiple_files(n_files=N_FILES)
    
    print("\n" + "="*70)
    print("🎯 PROCHAINES ÉTAPES:")
    print("="*70)
    print("1. Vérifie les fichiers dans data_converted/")
    print("2. Lance: python verify_conversion.py")
    print("3. Si OK, augmente N_FILES à 50 pour plus de données")
    print("4. Passe à la Phase 3: Adapter SGmVRNN\n")


if __name__ == "__main__":
    main()