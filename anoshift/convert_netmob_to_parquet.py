import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import os

INPUT_PATH = "~/Desktop/SIR/Datasets NetMob23"  # Dossier avec facebook/ et netflix/
OUTPUT_PATH = "~/Desktop/SIR/NetMob23_Parquet"  # Dossier de sortie


"""Génère les noms de colonnes : date + 96 intervalles de 15 minutes"""
def generate_column_names():
    columns = ['date']
    
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            columns.append(f'traffic_{hour:02d}h{minute:02d}')
    
    return columns


"""Charge un fichier TXT NetMob23 et retourne un DataFrame"""
def load_txt_file(filepath):
    data = []
    
    with open(filepath, 'r') as f:
        for line in f:
            values = line.strip().split()
            if values and len(values) > 1:  # Ignore les lignes vides
                # Remplace 'nan' par NaN
                values = [np.nan if v.lower() == 'nan' else v for v in values]
                data.append(values)
    
    if not data:
        return None
    
    # Crée le DataFrame avec les noms de colonnes
    columns = generate_column_names()
    
    # Ajuste si le nombre de colonnes ne correspond pas
    if len(data[0]) < len(columns):
        # Complète avec NaN si moins de colonnes
        for row in data:
            while len(row) < len(columns):
                row.append(np.nan)
    elif len(data[0]) > len(columns):
        # Tronque si plus de colonnes
        data = [row[:len(columns)] for row in data]
    
    df = pd.DataFrame(data, columns=columns)
    
    # Convertit la date
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')
    
    # Convertit toutes les autres colonnes en numérique
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


""" Fusionne plusieurs tiles d'une application (fb/Netflix) en un seul DataFrame"""
def merge_tiles(app_name, num_tiles=None):
    
    input_path = Path(INPUT_PATH).expanduser()
    app_path = input_path / app_name / 'DL'
    
    # Recherche des fichiers
    files = sorted(list(app_path.glob('*.txt')))
    
    if num_tiles:
        files = files[:num_tiles]
    
    print(f"\n Fusion de {len(files)} tiles pour {app_name.upper()}")
    print(f"   Cela peut prendre quelques minutes...")
    
    all_dfs = []
    
    for filepath in tqdm(files, desc=f"Chargement {app_name}"): #Chargement avec barre de progression
        df = load_txt_file(filepath)
        if df is not None and not df.empty:
            # Ajoute l'identifiant du tile
            tile_id = filepath.stem.split('_')[-1]  # Chaque ligne sait de quel tile géographique elle vient
            df['tile_id'] = tile_id
            all_dfs.append(df)
    
    if not all_dfs:
        print(f" Aucune donnée trouvée pour {app_name}")
        return None
    
    # Fusionne tous les DataFrames (avec: date, tile_id et les 96 colonnes de trafic)
    merged_df = pd.concat(all_dfs, ignore_index=True)
    
    # Réorganise les colonnes (date et tile_id en premier)
    cols = ['date', 'tile_id'] + [col for col in merged_df.columns if col not in ['date', 'tile_id']]
    merged_df = merged_df[cols]
    
    # Trie par date
    merged_df = merged_df.sort_values('date').reset_index(drop=True)
    
    print(f"    {merged_df.shape[0]} lignes × {merged_df.shape[1]} colonnes")
    print(f"    Période: {merged_df['date'].min()} → {merged_df['date'].max()}")
    
    return merged_df


"""Crée un subset pour tests rapides (comme Kyoto subset)"""
def create_subset(df, sample_size=50000):

    if df is None or len(df) <= sample_size:
        return df
    
    # Créer un échantillon de 50 000 lignes pour tests rapides.
    return df.sample(n=sample_size, random_state=42).sort_values('date').reset_index(drop=True)


"""Conversion complète en Parquet"""
def convert_app_to_parquet(app_name, num_tiles=None, create_subsets=True):
    
    print(f"\n{'='*60}")
    print(f" CONVERSION {app_name.upper()} → PARQUET")
    print(f"{'='*60}")
    
    # Fusionne les tiles
    df_full = merge_tiles(app_name, num_tiles)
    
    if df_full is None:
        return
    
    # Crée les dossiers de sortie
    output_path = Path(OUTPUT_PATH).expanduser()
    full_path = output_path / 'full'
    subset_path = output_path / 'subset'
    
    full_path.mkdir(parents=True, exist_ok=True)
    subset_path.mkdir(parents=True, exist_ok=True)
    
    # Sauvegarde le dataset complet
    full_file = full_path / f'{app_name}_full.parquet'
    print(f"\n Sauvegarde du dataset complet...")
    df_full.to_parquet(full_file, index=False)
    print(f"    Sauvegardé: {full_file}")
    print(f"    Taille: {full_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Crée et sauvegarde le subset
    if create_subsets:
        print(f"\n Création du subset (50k échantillons)...")
        df_subset = create_subset(df_full)
        subset_file = subset_path / f'{app_name}_subset.parquet'
        df_subset.to_parquet(subset_file, index=False)
        print(f"    Sauvegardé: {subset_file}")
        print(f"    Taille: {subset_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Affiche des statistiques
    print(f"\n STATISTIQUES {app_name.upper()}:")
    print(f"   - Lignes: {len(df_full):,}")
    print(f"   - Colonnes: {len(df_full.columns)}")
    print(f"   - Période: {(df_full['date'].max() - df_full['date'].min()).days} jours")
    print(f"   - Tiles uniques: {df_full['tile_id'].nunique()}")
    print(f"   - Valeurs manquantes: {df_full.isna().sum().sum():,}")

def verify_parquet(parquet_file):
    """Vérifie qu'un fichier parquet est bien créé"""
    print(f"\n Vérification de {parquet_file.name}...")
    df = pd.read_parquet(parquet_file)
    print(f"    Chargement OK")
    print(f"    Shape: {df.shape}")
    print(f"    Colonnes: {list(df.columns[:5])}... (premiers 5)")
    print(f"\n   Aperçu:")
    print(df.head(3))
    return df

# === Programme principal ===
if __name__ == "__main__":
    print("\n" + "="*60)
    print(" CONVERTISSEUR NetMob23 TXT → PARQUET")
    print("="*60)
    
    # Configuration
    NUM_TILES_FACEBOOK = 100  # Nombre de tiles Facebook à utiliser (None = tous)
    NUM_TILES_NETFLIX = 100   # Nombre de tiles Netflix à utiliser (None = tous)
    
    print(f"\n  Configuration:")
    print(f"   - Input: {INPUT_PATH}")
    print(f"   - Output: {OUTPUT_PATH}")
    print(f"   - Tiles Facebook: {NUM_TILES_FACEBOOK or 'Tous'}")
    print(f"   - Tiles Netflix: {NUM_TILES_NETFLIX or 'Tous'}")
    
    # Convertit Facebook
    try:
        convert_app_to_parquet('facebook', num_tiles=NUM_TILES_FACEBOOK)
    except Exception as e:
        print(f" Erreur Facebook: {e}")
    
    # Convertit Netflix
    try:
        convert_app_to_parquet('netflix', num_tiles=NUM_TILES_NETFLIX)
    except Exception as e:
        print(f" Erreur Netflix: {e}")
    
    # Vérifie les fichiers créés
    output_path = Path(OUTPUT_PATH).expanduser()
    
    print(f"\n{'='*60}")
    print(" CONVERSION TERMINÉE !")
    print(f"{'='*60}")
    
    print(f"\n Fichiers créés dans: {output_path}")
    
    # Liste les fichiers créés
    for folder in ['full', 'subset']:
        folder_path = output_path / folder
        if folder_path.exists():
            print(f"\n   {folder}/")
            for file in folder_path.glob('*.parquet'):
                print(f"      - {file.name} ({file.stat().st_size / 1024 / 1024:.2f} MB)")
    
    print(f"\n Prochaines étapes:")
    print(f"   1. Copie le dossier 'NetMob23_Parquet' dans AnoShift/datasets/")
    print(f"   2. Modifie AnoShift pour charger ces fichiers")
    print(f"   3. Lance un test avec --ds netmob23")
