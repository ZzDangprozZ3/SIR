import os
import glob
import pandas as pd
import numpy as np
import pickle as pkl

# CONFIGURATION
INPUT_PATH = '/data'
OUTPUT_DIR = './data_collected'
OUTPUT_PREFIX = 'netmob_' 
SERVICE_NAME = 'top_tiles' 

# Limite du nombre de noeuds car risque d'explosion combinatoire
TOP_N = 15  

def load_netmob_data(path, top_n=TOP_N):
    print(f"Chargement des données NetMob depuis {path}")
    
    files = glob.glob(os.path.join(path, '**/*.txt'), recursive=True)
    
    if not files:
        print("ERREUR: Aucun fichier .txt trouvé dans /data.")
        return None

    print(f"{len(files)} fichiers trouvés. Lecture en cours...")

    all_series = {}
    duplicates_count = 0
    
    for i, fpath in enumerate(files):
        # ID unique basé sur le nom du fichier
        file_name = os.path.basename(fpath)
        unique_id = file_name.replace('.txt', '')
        
        # Gestion doublons
        if unique_id in all_series:
            parent_folder = os.path.basename(os.path.dirname(fpath))
            unique_id = f"{parent_folder}_{unique_id}"
            duplicates_count += 1

        full_series = []
        try:
            with open(fpath, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) > 2:
                        # Lecture données (exclusion de la date)
                        day_data = [float(x) for x in parts[1:]]
                        full_series.extend(day_data)
            
            if len(full_series) > 0:
                all_series[unique_id] = full_series

        except Exception as e:
            print(f"Erreur lecture {unique_id}: {e}")

        if i % 100 == 0:
            print(f"   {i}/{len(files)} traités...", end='\r')

    print(f"\nLecture terminée. {duplicates_count} conflits de noms résolus.")

    # Création DataFrame (Temps x Tuiles)
    df = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in all_series.items() ]))
    df = df.fillna(0)
    
    print(f"Dimensions brutes : {df.shape}")

    # SÉLECTION DES TOP NOEUDS 
    top_nodes = df.sum().sort_values(ascending=False).head(top_n).index
    df_final = df[top_nodes]
    
    print(f"Sélection des {top_n} noeuds les plus actifs : {list(top_nodes)}")
    
    return df_final

def save_for_causalrca(df):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Nom final : netmob_top_tiles.pkl
    filename = f"{OUTPUT_PREFIX}{SERVICE_NAME}.pkl"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    print(f"Sauvegarde du Pickle : {filepath}")
    with open(filepath, 'wb') as f:
        pkl.dump(df, f)
    
    print("Conversion Terminée0")

if __name__ == "__main__":
    df = load_netmob_data(INPUT_PATH, top_n=TOP_N)
    if df is not None:
        save_for_causalrca(df)