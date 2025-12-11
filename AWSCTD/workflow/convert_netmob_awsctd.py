import pandas as pd
import numpy as np
import glob
import os
import sys

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.abspath(os.path.join(BASE_DIR, '../../netmob23/'))
OUTPUT_FILE = os.path.join(BASE_DIR, 'netmob_for_awsctd.csv')

# --- OPTION DE TEST RAPIDE ---
# Mettre un nombre pour tester vite, ou None pour tout traiter
MAX_FILES = 500

# Paramètres AWSCTD
VOCAB_SIZE = 100    
FIXED_LENGTH = 100 

# --- DICTIONNAIRE DES ANOMALIES (Labels = 1) ---
ANOMALY_DATES = {
    "20190422": 1, "20190501": 1, "20190508": 1, "20190530": 1, # Fériés
    "20190414": 1, "20190421": 1, "20190428": 1, # Dimanches vacances
    "20190512": 1, # Match
}

def load_data(path):
    print(f"Recherche dans : {path}")
    if not os.path.exists(path):
        print(f"ERREUR : Dossier introuvable.")
        sys.exit()

    files = glob.glob(os.path.join(path, '**/*.txt'), recursive=True)
    if not files:
        print("Erreur : Aucun fichier .txt trouvé.")
        sys.exit()

    # --- GESTION DE LA LIMITE ---
    if MAX_FILES is not None:
        print(f" MODE TEST : Traitement limité aux {MAX_FILES} premiers fichiers.")
        files = files[:MAX_FILES]
    else:
        print(f"MODE PRODUCTION : Traitement de tous les fichiers ({len(files)}).")

    print(f"Lecture en cours...")
    sequences = []
    dates_found = []

    for i, file in enumerate(files):
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
                            dates_found.append(date_str)
                    except ValueError:
                        continue 
        except Exception:
            pass
        
        if i % 50 == 0:
            print(f"   ... {i}/{len(files)} traités", end='\r')

    print(f"\n{len(sequences)} séquences extraites.")
    return sequences, dates_found

def process_sequences(sequences, vocab_size, fixed_len):
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

def add_labels_and_save(df, dates_list):
    print(" Ajout des Labels...")
    labels = [ANOMALY_DATES.get(d, 0) for d in dates_list]
    df['Label'] = labels
    
    count_anom = sum(labels)
    print(f"   -> Anomalies : {count_anom} / {len(df)} ({(count_anom/len(df))*100:.2f}%)")
    
    print(f"Sauvegarde : {OUTPUT_FILE}")
    # Séparateur virgule standard
    df.to_csv(OUTPUT_FILE, index=False, header=False, sep=',')
    print("Terminé.")

if __name__ == "__main__":
    seqs, dates = load_data(INPUT_PATH)
    df_clean = process_sequences(seqs, VOCAB_SIZE, FIXED_LENGTH)
    add_labels_and_save(df_clean, dates)