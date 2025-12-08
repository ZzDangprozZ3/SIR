import pandas as pd
import numpy as np
import glob
import os

# --- CONFIGURATION ---
# Mets ici le chemin racine où sont tes dossiers facebook_dl, netflix_dl
# ex: "C:/Users/hibik/Documents/Insa/4TC_SIR/Work/SIR/dataset/"
ROOT_PATH = './' 

OUTPUT_FILE = 'netmob_for_awsctd.csv'
FIXED_LENGTH = 100   # On garde 100 points temporels par jour
VOCAB_SIZE = 100     # On réduit les valeurs entre 0 et 100 (pour AWSCTD)
ANOMALY_RATE = 0.1   # 10% d'anomalies
MAX_SAMPLES = 50000  # <--- IMPORTANT : Limite pour ne pas saturer la RAM (mets None pour tout prendre)

def process_file(filepath):
    """Lit un fichier NetMob et retourne une liste de listes"""
    data = []
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) > 1: # Sécurité contre les lignes vides
                # On ignore la date (col 0) et on tente de convertir le reste
                try:
                    traffic = [float(x) for x in parts[1:]]
                    if len(traffic) > 0:
                        data.append(traffic)
                except ValueError:
                    continue # On saute les lignes mal formées
    except Exception as e:
        print(f"Erreur lecture fichier {filepath}: {e}")
        
    return data

# 1. Chargement des données
all_sequences = []
print("Recherche des fichiers...")
files = glob.glob(os.path.join(ROOT_PATH, '**/*.txt'), recursive=True)

print(f"{len(files)} fichiers trouvés. Lecture en cours...")

for i, f in enumerate(files):
    seqs = process_file(f)
    all_sequences.extend(seqs)
    
    # Arrêt anticipé si on a assez de données pour tester
    if MAX_SAMPLES is not None and len(all_sequences) > MAX_SAMPLES:
        all_sequences = all_sequences[:MAX_SAMPLES]
        print(f"Limite de {MAX_SAMPLES} échantillons atteinte. Arrêt de la lecture.")
        break
    
    if i % 100 == 0:
        print(f"{i} fichiers traités...", end='\r')

print(f"\nNombre final de jours récupérés : {len(all_sequences)}")

if len(all_sequences) == 0:
    print("ERREUR : Aucune donnée récupérée. Vérifie le chemin de tes fichiers.")
    exit()

# 2. Pre-processing
print("Traitement des séquences...")
processed_data = []
for seq in all_sequences:
    # Padding ou Truncating
    if len(seq) < FIXED_LENGTH:
        seq = seq + [0] * (FIXED_LENGTH - len(seq))
    else:
        seq = seq[:FIXED_LENGTH]
    processed_data.append(seq)

df = pd.DataFrame(processed_data)

# --- CORRECTION DU BUG "IntCastingNaNError" ---
print("Nettoyage des données (NaN/Inf)...")
df = df.fillna(0) # Remplace les vides par 0
df = df.replace([np.inf, -np.inf], 0) # Remplace l'infini par 0

# QUANTIZATION
max_val = df.max().max()
print(f"Valeur max globale : {max_val}")

if max_val == 0:
    print("Attention: Toutes les données sont à 0. Vérifie tes fichiers.")
    max_val = 1 # Pour éviter division par zéro

print("Conversion (Quantization)...")
# On force le calcul en float puis on convertit en int proprement
df = (df / max_val * (VOCAB_SIZE - 1))
df = df.fillna(0).astype(int) # Double sécurité avant le cast

# 3. Injection d'Anomalies
df['Label'] = 0
n_anomalies = int(len(df) * ANOMALY_RATE)
if n_anomalies > 0:
    print(f"Injection de {n_anomalies} anomalies...")
    anomaly_indices = np.random.choice(df.index, n_anomalies, replace=False)
    
    for idx in anomaly_indices:
        if np.random.rand() > 0.5:
            df.iloc[idx, 0:FIXED_LENGTH] = 0 # Blackout
        else:
            df.iloc[idx, 0:FIXED_LENGTH] = VOCAB_SIZE - 1 # Surcharge
        df.at[idx, 'Label'] = 1

# 4. Sauvegarde
print(f"Sauvegarde dans {OUTPUT_FILE}...")
df.to_csv(OUTPUT_FILE, index=False, header=False)
print("Terminé ! Tu peux lancer AWSCTD.py.")