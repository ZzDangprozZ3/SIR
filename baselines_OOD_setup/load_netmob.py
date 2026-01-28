import pandas as pd
import numpy as np
import os
import sys

def load_data(anoshift_db_path, app_name, ds_size):
    """Charge le fichier parquet unique selon l'application et la taille"""
    file_path = os.path.join(anoshift_db_path, ds_size, f"{app_name}_{ds_size}.parquet")
    if not os.path.exists(file_path):
        print(f"Erreur : Fichier introuvable -> {file_path}")
        sys.exit(-1)
    return pd.read_parquet(file_path).reset_index(drop=True)

def get_train(anoshift_db_path, app_name, ds_size, train_data_percent=0.7):
    df = load_data(anoshift_db_path, app_name, ds_size)
    traffic_cols = df.columns[1:97] 
    split_idx = int(len(df) * train_data_percent)
    df_train = df.iloc[:split_idx]
    
    # Extraction et conversion
    X_train = df_train[traffic_cols].to_numpy()
    
    # --- NETTOYAGE CRITIQUE ---
    # 1. Remplacer NaN par 0
    X_train = np.nan_to_num(X_train, nan=0.0, posinf=0.0, neginf=0.0)
    # 2. Forcer float32
    X_train = X_train.astype(np.float32)
    # 3. Écrêter les valeurs extrêmes qui font crash float32 (Cap à 1e10)
    X_train = np.clip(X_train, -1e10, 1e10)
    
    data_mean = X_train.mean(0)[None, :]
    data_std = X_train.std(0)[None, :]
    data_std[data_std == 0] = 1

    return X_train, data_mean, data_std

def get_test(anoshift_db_path, app_name, ds_size, train_data_percent=0.7):
    """Prépare les données de test (30% restants) et récupère les dates"""
    df = load_data(anoshift_db_path, app_name, ds_size)
    
    split_idx = int(len(df) * train_data_percent)
    df_test = df.iloc[split_idx:]
    
    traffic_cols = df.columns[1:97]
    test_dates = df.iloc[split_idx:, 0].values # Colonne 0 = Date/Timestamp
    
    X_test = df_test[traffic_cols].to_numpy()
    X_test = np.nan_to_num(X_test).astype(np.float32)
    
    # Label optionnel à la colonne 97
    y_test = df.iloc[split_idx:, -1].values if df.shape[1] > 97 else None
    
    return X_test, y_test, test_dates