import os
import glob
import pandas as pd
import numpy as np
import pickle as pkl
import random
import configparser
import sys

# CHARGEMENT CONFIGURATION
config = configparser.ConfigParser()
if not os.path.exists('config.ini'):
    print("ERREUR CRITIQUE: Fichier config.ini introuvable !")
    sys.exit(1)

config.read('config.ini')

try:
    INPUT_PATH = config['PATHS']['input_data']
    OUTPUT_DIR = config['PATHS']['output_dir']
    OUTPUT_PREFIX = config['PATHS']['output_prefix']
    SERVICE_NAME = config['PATHS']['service_name']
    
    TOP_N = config.getint('DATA', 'top_n')
    RANDOM_SAMPLING = config.getboolean('DATA', 'random_sampling')
    SAMPLE_POOL_SIZE = config.getint('DATA', 'sample_pool_size')
except KeyError as e:
    print(f"ERREUR CONFIG: Paramètre manquant dans config.ini -> {e}")
    sys.exit(1)

# FONCTIONS

def get_file_activity(fpath):
    """Lit un fichier et retourne seulement sa somme totale (activité)"""
    total_traffic = 0.0
    try:
        with open(fpath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) > 2:
                    vals = [float(x) for x in parts[1:]]
                    total_traffic += sum(vals)
    except Exception:
        return 0.0
    return total_traffic

def load_netmob_optimized():
    print(f" 1. Recensement des fichiers dans {INPUT_PATH} ")
    files = glob.glob(os.path.join(INPUT_PATH, '**/*.txt'), recursive=True)
    
    if not files:
        print("ERREUR: Aucun fichier trouvé.")
        return None

    print(f"   > {len(files)} fichiers trouvés.")

    #  PASSE 1 : SCORING 
    print("2. Calcul de l'activité des fichiers...")
    file_scores = []
    
    for i, fpath in enumerate(files):
        score = get_file_activity(fpath)
        if score > 0:
            file_scores.append((fpath, score))
        
        if i % 100 == 0:
            print(f"   Scan: {i}/{len(files)}...", end='\r')
            
    print(f"\n   > Scan terminé. {len(file_scores)} fichiers valides.")

    # SELECTION
    file_scores.sort(key=lambda x: x[1], reverse=True)

    selected_files = []
    if RANDOM_SAMPLING and len(file_scores) > SAMPLE_POOL_SIZE:
        pool = file_scores[:SAMPLE_POOL_SIZE]
        selected_files = random.sample(pool, TOP_N)
        print(f"3. Sélection ALÉATOIRE de {TOP_N} tuiles parmi le Top {SAMPLE_POOL_SIZE}")
    else:
        selected_files = file_scores[:TOP_N]
        print(f"3. Sélection des {TOP_N} tuiles les plus actives")

    # PASSE 2 : CHARGEMENT
    print("4. Chargement des données sélectionnées...")
    final_data = {}
    
    for fpath, score in selected_files:
        file_name = os.path.basename(fpath)
        unique_id = file_name.replace('.txt', '')
        
        if unique_id in final_data:
            parent = os.path.basename(os.path.dirname(fpath))
            unique_id = f"{parent}_{unique_id}"

        full_series = []
        with open(fpath, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) > 2:
                    day_data = [float(x) for x in parts[1:]]
                    full_series.extend(day_data)
        
        final_data[unique_id] = full_series
        print(f"   + Chargé: {unique_id} (Vol: {int(score)})")

    df = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in final_data.items() ]))
    df = df.fillna(0)
    
    print(f"Forme finale : {df.shape}")
    return df

def save_for_causalrca(df):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    filename = f"{OUTPUT_PREFIX}{SERVICE_NAME}.pkl"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    print(f"Sauvegarde : {filepath}")
    with open(filepath, 'wb') as f:
        pkl.dump(df, f)
    print("CONVERSION TERMINÉE")

if __name__ == "__main__":
    df = load_netmob_optimized()
    if df is not None:
        save_for_causalrca(df)