import pandas as pd
import numpy as np
import glob
import os
import sys
import configparser

# CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists('/data'):
    INPUT_PATH = '/data'
else:
    # Fallback pour test local sans Docker
    INPUT_PATH = os.path.abspath(os.path.join(BASE_DIR, '../../NetMob23/'))

OUTPUT_FILE = os.path.join(BASE_DIR, 'netmob_for_awsctd.csv')
OUTPUT_META_FILE = os.path.join(BASE_DIR, 'netmob_metadata.csv')

ANOMALY_FILE = os.path.join(BASE_DIR, 'anomalies.txt')

config_path = os.path.join(BASE_DIR, 'config.ini')
if os.path.exists(config_path):
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        # On lit la valeur ou on garde 500 si absente
        MAX_FILES = config.getint('MAIN', 'nMaxFiles', fallback=500)
        print(f"[CONFIG] Limite de fichiers chargée depuis config.ini : {MAX_FILES}")
    except Exception as e:
        print(f"[WARNING] Erreur lecture config.ini : {e}. Utilisation défaut : {MAX_FILES}")
else:
    print("[WARNING] config.ini introuvable. Utilisation défaut : 500")

# Paramètres AWSCTD
VOCAB_SIZE = 100


def detect_sequence_length(files):
    """Scanne le premier fichier valide pour déterminer la longueur standard"""
    for file in files:
        try:
            with open(file, 'r') as f:
                line = f.readline()
                parts = line.strip().split()
                if len(parts) > 2:
                    detected_len = len(parts) - 1
                    print(f"📏 Auto-detection de la longueur : {detected_len} mesures")
                    return detected_len
        except:
            continue
    return 96 # Valeur par défaut si échec

# DICTIONNAIRE DES ANOMALIES (Labels = 1)
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
    if not files:
        print("Erreur : Aucun fichier .txt trouvé.")
        sys.exit()

    # GESTION DE LA LIMITE
    if MAX_FILES is not None:
        print(f" MODE TEST : Traitement limité aux {MAX_FILES} premiers fichiers.")
        files = files[:MAX_FILES]
    else:
        print(f"MODE PRODUCTION : Traitement de tous les fichiers ({len(files)}).")

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
    """Nettoie, normalise et discrétise les séquences."""
    print(" Discrétisation (0-99)...")
    if not sequences:
        print("Erreur: Aucune séquence à traiter.")
        sys.exit()

    processed_seqs = []
    
    for seq in sequences:
        if len(seq) >= fixed_len:
            processed_seqs.append(seq[:fixed_len])
        else:
            processed_seqs.append(seq + [0] * (fixed_len - len(seq)))
            
    df = pd.DataFrame(processed_seqs)
    
    # Log Transform + MinMax Scaling
    df_log = np.log1p(df)
    min_val = df_log.min().min()
    max_val = df_log.max().max()
    
    if max_val == min_val:
        df_discrete = df_log * 0
    else:
        df_discrete = ((df_log - min_val) / (max_val - min_val)) * (vocab_size - 1)
    
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
    df_meta['Label'] = labels # On garde aussi le label pour vérification
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