import pandas as pd
import numpy as np
import glob
import os
import sys
import configparser
import random
from collections import Counter

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, 'config.ini')

# Valeurs par défaut
MAX_FILES = 500
VOCAB_SIZE = 100
SEQ_LEN_DEFAULT = 96
OUTPUT_CSV_NAME = 'netmob_for_awsctd.csv'
OUTPUT_META_NAME = 'netmob_metadata.csv'
ANOMALIES_NAME = 'anomalies.txt'
LOCAL_DATA_PATH = '../../NetMob23/'

if os.path.exists(config_path):
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        
        max_files_str = config.get('MAIN', 'nMaxFiles', fallback='500')
        if max_files_str.lower() == 'none':
            MAX_FILES = None
        else:
            try:
                MAX_FILES = int(max_files_str)
            except ValueError:
                print(f"WARNING : Valeur '{max_files_str}' invalide. Utilisation de None.")
                MAX_FILES = None
        

        # Lecture DATA
        VOCAB_SIZE = config.getint('DATA', 'nVocabSize', fallback=VOCAB_SIZE)
        SEQ_LEN_DEFAULT = config.getint('DATA', 'nSequenceLength', fallback=SEQ_LEN_DEFAULT)
        LOCAL_DATA_PATH = config.get('DATA', 'sLocalDataPath', fallback=LOCAL_DATA_PATH)

        # Lecture FILES 
        OUTPUT_CSV_NAME = config.get('FILES', 'sOutputCSV', fallback=OUTPUT_CSV_NAME)
        OUTPUT_META_NAME = config.get('FILES', 'sOutputMeta', fallback=OUTPUT_META_NAME)
        ANOMALIES_NAME = config.get('FILES', 'sAnomalies', fallback=ANOMALIES_NAME)
        
        print(f"CONFIG : Chargée. MaxFiles: {MAX_FILES}, Vocab: {VOCAB_SIZE}")
    except Exception as e:
        print(f"WARNING : Erreur config.ini : {e}")

# Mise à jour des chemins avec les variables
if os.path.exists('/data'):
    INPUT_PATH = '/data'
else:
    INPUT_PATH = os.path.abspath(os.path.join(BASE_DIR, LOCAL_DATA_PATH))

OUTPUT_FILE = os.path.join(BASE_DIR, OUTPUT_CSV_NAME)
OUTPUT_META_FILE = os.path.join(BASE_DIR, OUTPUT_META_NAME)
ANOMALY_FILE = os.path.join(BASE_DIR, ANOMALIES_NAME)


def detect_sequence_length(files, sample_size=50):
    """
    Scanne un échantillon aléatoire de fichiers pour trouver la longueur de séquence la plus fréquente (Mode).
    """
    if not files:
        return SEQ_LEN_DEFAULT

    # Echantillons aléatoire (tout si < 50 fichiers)
    nb_files_to_scan = min(len(files), sample_size)
    selected_files = random.sample(files, nb_files_to_scan)
    
    detected_lengths = []
    
    print(f"Auto-détection de la longueur sur {nb_files_to_scan} fichiers...")

    for file in selected_files:
        try:
            with open(file, 'r') as f:
                line = f.readline() # lecture de la première ligne
                parts = line.strip().split()
                # Vérification de la présence d'au moins une date + 2 colonnes de données
                if len(parts) > 2:
                    detected_lengths.append(len(parts) - 1)
        except:
            continue
    
    if not detected_lengths:
        print("WARNING : Impossible de lire les fichiers. Utilisation de la valeur par défaut.")
        return SEQ_LEN_DEFAULT

    # Calcul de la valeur la plus fréquente (Mode)
    counts = Counter(detected_lengths)
    most_common_len, freq = counts.most_common(1)[0]
    
    print(f" Longueur retenue : {most_common_len} (Apparait {freq}/{len(detected_lengths)} fois)")
    
    if len(counts) > 1:
        print(f"   WARNING : Disparité détectée ! Autres longueurs trouvées : {dict(counts)}")
        print(f"   Les séquences seront coupées ou paddées à {most_common_len}.")

    return most_common_len

# Dictionnaire des anomalies (Labels = 1)
def load_anomalies(file_path):
    """Charge les dates d'anomalies depuis un fichier texte."""
    if not os.path.exists(file_path):
        print(f"Fichier d'anomalies {file_path} introuvable. Aucune anomalie marquée.")
        return {}
    
    with open(file_path, 'r') as f:
        return {line.strip(): 1 for line in f if line.strip()}

def load_data(path):
    """Charge les données depuis les fichiers texte dans le répertoire spécifié."""
    print(f"Recherche dans : {path}")
    if not os.path.exists(path):
        print(f"ERREUR : Dossier introuvable.")
        sys.exit()

    files = glob.glob(os.path.join(path, '**/*.txt'), recursive=True)
    files.sort()
    if not files:
        print("Erreur : Aucun fichier .txt trouvé.")
        sys.exit()

    # Gestion de la limite de fichiers
    if MAX_FILES is not None:
        print(f"Traitement limité aux {MAX_FILES} premiers fichiers.")
        files = files[:MAX_FILES]
    else:
        print(f"Traitement de tous les fichiers ({len(files)}).")

    print(f"Lecture en cours...")
    sequences = []
    metadata = []


    for i, file in enumerate(files):
        filename = os.path.basename(file)
        try:
            with open(file, 'r') as f:
                lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if len(parts) > 2: 
                    date_str = parts[0]
                    try:
                        traffic_seq = [float(x) for x in parts[1:]]
                        if len(traffic_seq) > 10: 
                            sequences.append(traffic_seq)
                            metadata.append({'Date': date_str, 'Tile': filename})
                    except ValueError:
                        continue 
        except Exception:
            pass
        
        if i % 50 == 0:
            print(f"   ... {i}/{len(files)} traités", end='\r')

    print(f"\n{len(sequences)} séquences extraites.")
    return sequences, metadata

def process_sequences(sequences, vocab_size, fixed_len):
    """Nettoie, normalise et discrétise les séquences"""
    print(" Discrétisation (0-99)")
    if not sequences:
        print("Erreur: Aucune séquence à traiter.")
        sys.exit()

    processed_seqs = []
    
    # Mise en forme à longueur fixe
    for seq in sequences:
        if len(seq) >= fixed_len:
            processed_seqs.append(seq[:fixed_len])
        else:
            processed_seqs.append(seq + [0] * (fixed_len - len(seq)))
            
    df = pd.DataFrame(processed_seqs)
    
    df_log = np.log1p(df)
    
    # Determination du min/max sur la première moitié des données
    calibration_ratio = 0.5 
    split_index = int(len(df_log) * calibration_ratio)
    
    calibration_data = df_log.iloc[:split_index]
    
    min_val = calibration_data.min().min()
    max_val = calibration_data.max().max()
    
    print(f" Min: {min_val:.4f}, Max: {max_val:.4f} (sur {split_index} séquences)")
    
    # Normalisation du dataset
    if max_val == min_val:
        df_discrete = df_log * 0
    else:
        df_normalized = (df_log - min_val) / (max_val - min_val)
        
        df_scaled = df_normalized * (vocab_size - 1)
        
        df_discrete = df_scaled.clip(0, vocab_size - 1)
    
    return df_discrete.fillna(0).astype(int)

def add_labels_and_save(df,dates_list, metadata,ANOMALY_DATES):
    """Ajoute les labels et sauvegarde les données."""
    print(" Ajout des Labels...")
    labels = [ANOMALY_DATES.get(d, 0) for d in dates_list]
    df['Label'] = labels
    
    count_anom = sum(labels)
    print(f"   -> Anomalies : {count_anom} / {len(df)} ({(count_anom/len(df))*100:.2f}%)")
    
    print(f"Sauvegarde : {OUTPUT_FILE}")
    df.to_csv(OUTPUT_FILE, index=False, header=False, sep=',')

    # Sauvegarde des métadonnées
    df_meta = pd.DataFrame(metadata)
    df_meta['Label'] = labels
    df_meta.to_csv(OUTPUT_META_FILE, index=True, index_label='Index')

    print("Terminé.")

if __name__ == "__main__":
    ANOMALY_DATES = load_anomalies(ANOMALY_FILE)
    files = glob.glob(os.path.join(INPUT_PATH, '**/*.txt'), recursive=True)
    DYNAMIC_LENGTH = detect_sequence_length(files)

    seqs, metadata = load_data(INPUT_PATH)
    df_clean = process_sequences(seqs, VOCAB_SIZE, DYNAMIC_LENGTH)
    dates_list = [m['Date'] for m in metadata]
    add_labels_and_save(df_clean,dates_list, metadata,ANOMALY_DATES)