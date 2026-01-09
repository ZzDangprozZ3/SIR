import os
import glob
import pandas as pd
import numpy as np
import pickle as pkl
import random
import configparser
import sys
import math

# CONFIGURATION
config = configparser.ConfigParser()
if os.path.exists('config.ini'):
    config.read('config.ini')
    INPUT_PATH = config.get('PATHS', 'input_data', fallback='/data')
    OUTPUT_DIR = config.get('PATHS', 'output_dir', fallback='./data_collected')
    OUTPUT_PREFIX = config.get('PATHS', 'output_prefix', fallback='netmob_')
    SERVICE_NAME = config.get('PATHS', 'service_name', fallback='top_tiles')
    TOP_N = config.getint('DATA', 'top_n', fallback=15)
else:
    INPUT_PATH = '/data'
    OUTPUT_DIR = './data_collected'
    OUTPUT_PREFIX = 'netmob_'
    SERVICE_NAME = 'top_tiles'
    TOP_N = 15

def safe_float_sum(str_vals):
    """Convertit une liste de strings en somme de floats"""
    total = 0.0
    for x in str_vals:
        try:
            if 'nan' in x.lower():
                continue
            val = float(x)
            if not math.isnan(val):
                total += val
        except ValueError:
            continue
    return total

def load_netmob_data():
    print(f" 1. Recensement des fichiers dans {INPUT_PATH} ", flush=True)
    files = glob.glob(os.path.join(INPUT_PATH, '**/*.txt'), recursive=True)
    
    if not files:
        print("ERREUR: Aucun fichier trouvé.", flush=True)
        return None

    print(f"   > {len(files)} fichiers trouvés.", flush=True)

    # PASSE 1 : SCORING
    print(" 2. Calcul de l'activité ", flush=True)
    file_scores = []
    
    for i, fpath in enumerate(files):
        total_traffic = 0.0
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        total_traffic += safe_float_sum(parts[1:])
        except Exception as e:
            print(f"[ERREUR LECTURE] {os.path.basename(fpath)} : {e}", flush=True)
            
        if total_traffic > 0:
            file_scores.append((fpath, total_traffic))
        else:
            if i == 0:
                 print(f"[DEBUG] Le premier fichier a toujours 0 trafic après correction. Vérifier contenu: {fpath}", flush=True)

        if i % 2000 == 0:
            print(f"   Scan: {i}/{len(files)}...", end='\r', flush=True)
            
    print(f"\n   > Scan terminé. {len(file_scores)} fichiers valides.", flush=True)
    
    if not file_scores:
        print("ERREUR CRITIQUE : Aucun fichier valide retenu.", flush=True)
        return None

    # SELECTION & CHARGEMENT FINAL
    print(f" 3. Sélection des {TOP_N} tuiles les plus actives ", flush=True)
    file_scores.sort(key=lambda x: x[1], reverse=True)
    selected_files = file_scores[:TOP_N]

    final_data = {}
    print(" 4. Chargement complet ", flush=True)
    
    for fpath, score in selected_files:
        file_name = os.path.basename(fpath)
        unique_id = file_name.replace('.txt', '')
        
        if unique_id in final_data:
            parent = os.path.basename(os.path.dirname(fpath))
            unique_id = f"{parent}_{unique_id}"

        full_series = []
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 2:
                    row_data = []
                    for x in parts[1:]:
                        try:
                            if 'nan' in x.lower():
                                row_data.append(0.0)
                            else:
                                val = float(x)
                                row_data.append(0.0 if math.isnan(val) else val)
                        except:
                            row_data.append(0.0)
                    full_series.extend(row_data)
        
        final_data[unique_id] = full_series
        print(f"   + {unique_id} (Vol: {int(score)})", flush=True)

    # Conversion DataFrame
    df = pd.DataFrame(dict([ (k,pd.Series(v)) for k,v in final_data.items() ]))
    df = df.fillna(0)
    
    print(f" Forme finale : {df.shape} ", flush=True)
    return df

def save_for_causalrca(df):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    filename = f"{OUTPUT_PREFIX}{SERVICE_NAME}.pkl"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    print(f"Sauvegarde : {filepath}", flush=True)
    with open(filepath, 'wb') as f:
        pkl.dump(df, f)
    print(" CONVERSION TERMINÉE ", flush=True)

if __name__ == "__main__":
    df = load_netmob_data()
    if df is not None:
        save_for_causalrca(df)