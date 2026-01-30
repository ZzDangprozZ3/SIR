import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, required=True)
args = parser.parse_args()

INPUT_PATH = args.input
OUTPUT_PATH = "./datasets/NetMob23_Parquet"

def generate_column_names():
    columns = ['date']
    for hour in range(24):
        for minute in [0, 15, 30, 45]:
            columns.append(f'traffic_{hour:02d}h{minute:02d}')
    return columns

def load_txt_file(filepath):
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            values = line.strip().split()
            if values and len(values) > 1:
                values = [np.nan if v.lower() == 'nan' else v for v in values]
                data.append(values)
    if not data:
        return None
    columns = generate_column_names()
    if len(data[0]) < len(columns):
        for row in data:
            while len(row) < len(columns):
                row.append(np.nan)
    elif len(data[0]) > len(columns):
        data = [row[:len(columns)] for row in data]
    df = pd.DataFrame(data, columns=columns)
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d', errors='coerce')
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def merge_tiles(app_name):
    input_path = Path(INPUT_PATH)
    
    possible_paths = [
        input_path / app_name / 'DL',
        input_path / app_name,
        input_path / app_name.capitalize() / 'DL',
        input_path / app_name.capitalize(),
    ]
    
    app_path = None
    for p in possible_paths:
        if p.exists():
            app_path = p
            break
    
    if app_path is None:
        print(f"Dossier introuvable pour {app_name}")
        print(f"Chemins testés: {possible_paths}")
        return None
    
    files = sorted(list(app_path.glob('*.txt')))
    print(f"\nFusion de {len(files)} fichiers pour {app_name.upper()} depuis {app_path}")
    
    if len(files) == 0:
        print(f"Aucun fichier .txt trouvé dans {app_path}")
        return None
    
    all_dfs = []
    for filepath in tqdm(files, desc=f"Chargement {app_name}"):
        df = load_txt_file(filepath)
        if df is not None and not df.empty:
            tile_id = filepath.stem.split('_')[-1]
            df['tile_id'] = tile_id
            all_dfs.append(df)
    
    if not all_dfs:
        return None
    
    merged_df = pd.concat(all_dfs, ignore_index=True)
    cols = ['date', 'tile_id'] + [col for col in merged_df.columns if col not in ['date', 'tile_id']]
    merged_df = merged_df[cols]
    merged_df = merged_df.sort_values('date').reset_index(drop=True)
    print(f"   {merged_df.shape[0]} lignes × {merged_df.shape[1]} colonnes")
    return merged_df

def create_subset(df, sample_size=50000):
    if df is None or len(df) <= sample_size:
        return df
    return df.sample(n=sample_size, random_state=42).sort_values('date').reset_index(drop=True)

def convert_app_to_parquet(app_name):
    print(f"\n{'='*60}")
    print(f"CONVERSION {app_name.upper()}")
    print(f"{'='*60}")
    
    df_full = merge_tiles(app_name)
    if df_full is None:
        return
    
    output_path = Path(OUTPUT_PATH)
    full_path = output_path / 'full'
    subset_path = output_path / 'subset'
    full_path.mkdir(parents=True, exist_ok=True)
    subset_path.mkdir(parents=True, exist_ok=True)
    
    full_file = full_path / f'{app_name}_full.parquet'
    df_full.to_parquet(full_file, index=False)
    print(f"Sauvegardé: {full_file}")
    
    df_subset = create_subset(df_full)
    subset_file = subset_path / f'{app_name}_subset.parquet'
    df_subset.to_parquet(subset_file, index=False)
    print(f"Sauvegardé: {subset_file}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CONVERTISSEUR NetMob23 TXT → PARQUET")
    print("="*60)
    print(f"Input: {INPUT_PATH}")
    
    convert_app_to_parquet('facebook')
    convert_app_to_parquet('netflix')
    
    print(f"\nCONVERSION TERMINÉE !")
