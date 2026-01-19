import os
import glob
import pandas as pd
import numpy as np
import pickle as pkl
import configparser
import math
import json
import re
import argparse
import sys

# CONFIGURATION
config = configparser.ConfigParser()
if os.path.exists('config.ini'):
    config.read('config.ini')
    INPUT_PATH = config.get('PATHS', 'input_data', fallback='/data')
    OUTPUT_DIR = config.get('PATHS', 'output_dir', fallback='./data_collected')
    TOP_N = config.getint('DATA', 'top_n', fallback=15)
    
    GEOJSON_NAME = config.get('PATHS', 'geojson_file', fallback='Lyon.geojson')
    ANOMALIES_NAME = config.get('PATHS', 'anomalies_file', fallback='Anomalies_NetMob23.txt')
    
    GEOJSON_PATH = os.path.join(INPUT_PATH, GEOJSON_NAME)
else:
    INPUT_PATH = '/data'
    OUTPUT_DIR = './data_collected'
    TOP_N = 15
    GEOJSON_PATH = 'Lyon.geojson'

def safe_float_sum(str_vals):
    """Convertit une liste de strings en somme de floats"""
    total = 0.0
    for x in str_vals:
        try:
            val = float(x)
            floats.append(0.0 if math.isnan(val) else val)
        except:
            floats.append(0.0)
    return floats

def extract_tile_id(filename):
    base = os.path.basename(filename)
    match = re.search(r'(?:tile)[_\-\s]?(\d+)', base, re.IGNORECASE)

    if match:
        return int(match.group(1))
    
    return None

def load_geojson_centroids(geojson_path):
    print(f"   > Chargement GeoJSON : {geojson_path}")
    if not os.path.exists(geojson_path):
        print(f"     ERREUR : Le fichier GeoJSON est introuvable ici : {geojson_path}")
        print(f"     Contenu du dossier {os.path.dirname(geojson_path)} : {os.listdir(os.path.dirname(geojson_path))}")
        return None
    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)
        centroids = {}
        for feature in data.get('features', []):
            tid = feature.get('properties', {}).get('tile_id')
            coords = feature.get('geometry', {}).get('coordinates', [])
            if tid is not None and len(coords) > 0:
                centroids[int(tid)] = np.array(coords[0]).mean(axis=0)
        print(f"     {len(centroids)} tuiles géolocalisées chargées.")
        return centroids
    except Exception as e:
        print(f"     ERREUR : GeoJSON corrompu ou illisible : {e}")
        return None

def parse_anomaly_file(filepath):
    tasks = []
    print(f"   > Lecture du fichier d'anomalies : {filepath}")
    if not os.path.exists(filepath):
        print(f"ERREUR: Fichier {filepath} introuvable.")
        return []
        
    with open(filepath, 'r') as f:
        lines = f.readlines()
        print(f"     Le fichier contient {len(lines)} lignes.")
        for i, line in enumerate(lines):
            # Regex adaptée au format NetMob23
            match_date = re.search(r'Date:\s*(\d{8})', line)
            if not match_date:
            # Essai format simple (YYYYMMDD au début de ligne)
                match_date = re.search(r'^(\d{8})', line)

            match_tile = re.search(r'(?:tile)[_\-\s]*(\d+)', line, re.IGNORECASE)
            
            if match_date and match_tile:
                tasks.append({
                    'date': match_date.group(1),
                    'tile_id': int(match_tile.group(1)),
                    'original_line': line.strip()
                })

            else:
                # DEBUG : Affiche les 3 premières lignes rejetées pour comprendre pourquoi
                if i < 3: 
                    print(f"     [DEBUG REJET Ligne {i}] Date trouvée? {bool(match_date)} | Tile trouvée? {bool(match_tile)}")
                    print(f"     -> Contenu : {line.strip()}")

    print(f"   > {len(tasks)} anomalies détectées à traiter.")
    return tasks

def map_files_to_ids():
    print(f"   > Indexation des fichiers NetMob dans : {INPUT_PATH}")
    mapping = {} 
    search_pattern = os.path.join(INPUT_PATH, '**/*.txt')
    files = glob.glob(search_pattern, recursive=True)

    print(f"     {len(files)} fichiers .txt trouvés au total.")

    rejected_examples = []

    if len(files) == 0:
        print(f"     ERREUR : Aucun fichier .txt trouvé ! Vérifiez le montage Docker.")
        return {}
    
    for fpath in files:
        tid = extract_tile_id(fpath)
        if tid is not None:
            mapping[tid] = fpath
        else:
            if len(rejected_examples) < 5:
                rejected_examples.append(os.path.basename(fpath))
            
    print(f"     {len(mapping)} fichiers NetMob indexés avec succès (ID reconnus).")

    if len(mapping) == 0 and len(files) > 0:
        print("\n" + "="*50)
        print("[DIAGNOSTIC ECHEC INDEXATION]")
        print("Le script voit les fichiers mais n'arrive pas à lire l'ID dans le nom.")
        print("Voici 5 exemples de fichiers trouvés mais rejetés :")
        for ex in rejected_examples:
            print(f" - {ex}")
        print("="*50 + "\n")
    return mapping

def process_anomaly(task, centroids, file_mapping):
    target_tile = task['tile_id']
    target_date = task['date']
    
    if target_tile not in centroids:
        # print(f"Tile {target_tile} hors zone GeoJSON")
        return None
    
    seed_pos = centroids[target_tile]
    distances = []
    
    for tid, pos in centroids.items():
        dist = np.linalg.norm(pos - seed_pos)
        distances.append((tid, dist))
    
    distances.sort(key=lambda x: x[1])
    neighbor_ids = [d[0] for d in distances[:TOP_N]]
    
    raw_data = {}
    points_per_day = 0
    
    for tid in neighbor_ids:
        if tid not in file_mapping: continue
        fpath = file_mapping[tid]
        
        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.startswith(target_date):
                        vals = safe_float_convert(line.strip().split()[1:])
                        if len(vals) > 0:
                            raw_data[f"tile_{tid}"] = vals
                            points_per_day = max(points_per_day, len(vals))
                        break
        except: pass

    if not raw_data: return None

    final_dict = {}
    for uid, vals in raw_data.items():
        if len(vals) < points_per_day:
            vals += [0.0] * (points_per_day - len(vals))
        final_dict[uid] = vals
        
    df = pd.DataFrame(final_dict)
    df_norm = (df - df.mean()) / (df.std() + 1e-8)
    df_norm = df_norm.fillna(0)
    
    return df_norm

def save_output(df, date, tile_id):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    filename = f"anomaly_{date}_{tile_id}.pkl"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'wb') as f:
        pkl.dump(df, f)
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--anomalies_file', type=str, help='Chemin vers le fichier anomalies')
    args = parser.parse_args()

    if not os.path.exists(INPUT_PATH):
        print(f"ERREUR : Le dossier d'entrée {INPUT_PATH} n'existe pas dans le Docker.")
        sys.exit(1)

    target_file = None

    if args.anomalies_file:
        target_file = args.anomalies_file
        print(f"MODE : Fichier spécifié manuellement -> {target_file}")
    
    elif ANOMALIES_NAME:
        potential_path = os.path.join(INPUT_PATH, ANOMALIES_NAME)
        if os.path.exists(potential_path):
            target_file = potential_path
            print(f"MODE : Utilisation du fichier par défaut (Config) -> {target_file}")

    # Lecture des configs globales
    if target_file and os.path.exists(target_file):
        centroids = load_geojson_centroids(GEOJSON_PATH)
        file_mapping = map_files_to_ids()
        
        if centroids and file_mapping:
            tasks = parse_anomaly_file(target_file)
            
            if not tasks:
                print(f"[STOP] Le fichier {target_file} est vide ou mal formaté (0 anomalies trouvées).")
                sys.exit(0)
                
            count = 0
            print(f"   > Démarrage de la génération des matrices...")
            for task in tasks:
                df = process_anomaly(task, centroids, file_mapping)
                if df is not None:
                    save_output(df, task['date'], task['tile_id'])
                    count += 1
            print(f" {count} datasets générés sur {len(tasks)} demandés.")
        else:
             print("\n[ECHEC] Impossible de démarrer : GeoJSON ou Fichiers NetMob manquants.")
    else:
        print("="*60)
        print("[ERREUR] Aucun fichier d'anomalies valide trouvé.")
        print(f"1. Vérifiez que le fichier '{ANOMALIES_NAME}' est bien présent dans votre dossier de données local")
        print(f"2. Vérifiez que le nom dans 'config.ini' (clé anomalies_file) est exactement le même.")
        print("="*60)
        sys.exit(1)