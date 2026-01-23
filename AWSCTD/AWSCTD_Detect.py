import sys
import os
import pandas as pd
import numpy as np
import tensorflow as tf
from keras.models import load_model
from keras.utils import to_categorical

# CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.abspath(os.path.join(BASE_DIR, '../workflow/netmob_for_awsctd.csv'))
META_FILE = os.path.abspath(os.path.join(BASE_DIR, '../workflow/netmob_metadata.csv'))
MODEL_FILE = os.path.join(BASE_DIR, 'trained_model.keras')
REPORT_FILE = os.path.join(BASE_DIR, 'ANOMALY_REPORT.txt')
ALERTRCA_FILE = os.path.join(BASE_DIR, 'faults_AWSCTD.csv')

# Paramètres 
VOCAB_SIZE = 100 

def generate_report():
    if not os.path.exists(MODEL_FILE):
        print(f"Erreur: Modèle introuvable ({MODEL_FILE}). Lancez l'entraînement d'abord.")
        return
    
    try:
        model = load_model(MODEL_FILE)
    except Exception as e:
        print(f"Erreur chargement modèle: {e}")
        return
    data = pd.read_csv(DATA_FILE, header=None)
    
    X = data.iloc[:, :-1].values 
    
    X = to_categorical(X, num_classes=VOCAB_SIZE).astype('float16')
    

    meta = pd.read_csv(META_FILE)
    
    if len(meta) != len(X):
        print(f"ATTENTION : Le nombre de lignes Data ({len(X)}) diffère des Métadonnées ({len(meta)}) !")
    

    print("Analyse des anomalies en cours...")
    predictions = model.predict(X, verbose=1)
    

    print(f"\n[DEBUG STATS]")
    print(f"Min score : {predictions.min():.4f}")
    print(f"Max score : {predictions.max():.4f}")
    print(f"Moyenne   : {predictions.mean():.4f}")

    if predictions.shape[1] == 1:
        # Sortie binaire
        anomalies_indices = np.where(predictions > 0.5)[0]
        scores = predictions
    else:
        # Sortie catégorielle
        anomalies_indices = np.where(np.argmax(predictions, axis=1) == 1)[0]
        scores = predictions[:, 1]

    if predictions.shape[1] == 1:

        anomalies_indices = np.where(predictions > 0.5)[0]
        scores = predictions
    else:
        # Si categorical (2 neurones softmax), l'anomalie est la classe 1
        anomalies_indices = np.where(np.argmax(predictions, axis=1) == 1)[0]
        scores = predictions[:, 1] # Score de la classe 1


    print(f"\nANOMALIES TROUVÉES : {len(anomalies_indices)}")
    
    with open(REPORT_FILE, 'w') as f:
        f.write(f"Fichier analysé : {DATA_FILE}\n")
        f.write(f"Total séquences : {len(X)}\n")
        f.write(f"Anomalies détectées : {len(anomalies_indices)}\n")

        
        for idx in anomalies_indices:
            if idx < len(meta):
                row = meta.iloc[idx]
                tile = row['Tile']
                date = row['Date']
                score = scores[idx] if isinstance(scores[idx], float) else scores[idx][0]
                
                line = f"Date: {date} | Tile: {tile} | Confiance: {score:.4f}\n"
                f.write(line)
            else:
                f.write(f"ERREUR: Index {idx} hors limites des métadonnées.\n")

    print(f"Génération du CSV compatible AlertRCA : {ALERTRCA_FILE}")
    
    with open(ALERTRCA_FILE, 'w') as f_csv:
        f_csv.write("id,score\n")
        
        for idx in anomalies_indices:
            if idx < len(meta):
                row = meta.iloc[idx]
                
                tile_full = str(row['Tile'])
                date_val = str(row['Date'])
                score = scores[idx] if isinstance(scores[idx], float) else scores[idx][0]
                
                try:

                    parts = tile_full.split('_')
                    
                    app_name = parts[0]
                    
                    tile_id = parts[-1].replace('.txt', '')
                    
                    formatted_id = f"{app_name}_{tile_id}_{date_val}"
                    
                    f_csv.write(f"{formatted_id},{score:.6f}\n")
                    
                except Exception as e:
                    print(f"Erreur de formatage sur {tile_full}: {e}")

    print(f"Rapports générés avec succès.")

if __name__ == "__main__":
    generate_report()