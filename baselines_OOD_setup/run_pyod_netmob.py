import sys
import numpy as np
import load_netmob
import gc
from pyod.models.copod import COPOD

# Paramètres de sécurité RAM
BATCH_SIZE = 10000 
MAX_TRAIN_SAMPLES = 100000 

def run_experiment(method_name, app_name, ds_size):
    print("\n" + "="*60)
    print(f"NETMOB23 - {method_name.upper()} SUR {app_name.upper()} ({ds_size})")
    print("="*60)

    netmob_path = "../datasets/NetMob23_Parquet"

    # [1/3] CHARGEMENT TRAIN
    print("\n[1/3] CHARGEMENT TRAIN...")
    # APPEL SYNCHRONISÉ AVEC load_netmob.py (3 arguments)
    X_train, d_mean, d_std = load_netmob.get_train(netmob_path, app_name, ds_size)

    if len(X_train) > MAX_TRAIN_SAMPLES:
        print(f"  Sous-échantillonnage : {len(X_train):,} -> {MAX_TRAIN_SAMPLES:,}")
        np.random.seed(42)
        idx = np.random.choice(len(X_train), MAX_TRAIN_SAMPLES, replace=False)
        X_train = X_train[idx]

    clf = COPOD(n_jobs=1)
    print(f"  Entraînement de COPOD en cours...")
    # Vérification ultime de finitude
    if not np.isfinite(X_train).all():
        print("  [Alerte] Valeurs infinies détectées après échantillonnage. Nettoyage forcé...")
        X_train = np.nan_to_num(X_train)

    print(f"  Entraînement de COPOD en cours...")
    clf.fit(X_train)
    
    del X_train
    gc.collect()

    # [2/3] CHARGEMENT TEST & PRÉDICTION
    print("\n[2/3] CHARGEMENT TEST...")
    X_test, y_test, test_dates = load_netmob.get_test(netmob_path, app_name, ds_size)

    y_scores = []
    print(f"  Inférence par batch de {BATCH_SIZE}...")
    for i in range(0, len(X_test), BATCH_SIZE):
        batch = X_test[i:i+BATCH_SIZE]
        y_scores.append(clf.decision_function(batch))
        print(f"  Progression : {min(i+BATCH_SIZE, len(X_test)):,}/{len(X_test):,}", end="\r")
    
    y_scores = np.concatenate(y_scores)

    # [3/3] RÉSULTATS
    print("\n\n[3/3] ANALYSE DES ANOMALIES")
    s_mean, s_std = np.mean(y_scores), np.std(y_scores)
    top_10_idx = np.argsort(y_scores)[-10:][::-1]
    
    print("\n  TOP 10 JOURNÉES LES PLUS ANORMALES :")
    print("-" * 65)
    
    # Sauvegarde complète
    res_file = f"results_{app_name}_{ds_size}.txt"
    with open(res_file, "w") as f:
        f.write("=== STATISTIQUES GLOBALES ===\n")
        f.write(f"Min Score : {np.min(y_scores):.2f}\n")
        f.write(f"Max Score : {np.max(y_scores):.2f}\n")
        f.write(f"Moyenne   : {s_mean:.2f}\n")
        f.write(f"Std (Ecart-type) : {s_std:.2f}\n")
        f.write("\n=== TOP 10 ANOMALIES ===\n")
        f.write("Date | Score | Z-Score (Déviation)\n")
        
        for idx in top_10_idx:
            # --- NETTOYAGE DE LA DATE ---
            # On ne garde que la partie 'Day' (YYYY-MM-DD)
            clean_date = np.datetime_as_string(test_dates[idx], unit='D')
            
            # Calcul du Z-score
            z_score = (y_scores[idx] - s_mean) / s_std
            
            # Affichage console
            print(f"  Date: {clean_date} | Score: {y_scores[idx]:.2f} (+{z_score:.1f} std)")
            
            # Écriture fichier
            f.write(f"{clean_date}, {y_scores[idx]:.2f}, {z_score:.1f}\n")
    
    print("-" * 65)

    print(f"\nFichier généré : {res_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("\nUsage: python run_pyod_netmob.py copod <app> <size>")
        sys.exit(1)
    run_experiment(sys.argv[1].lower(), sys.argv[2].lower(), sys.argv[3].lower())