import pandas as pd
import numpy as np
import glob
import os
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIG ---
ROOT_PATH = './'  # Ton dossier
SAMPLE_SIZE = 1000 # On ne lit que 1000 jours pour aller vite

def load_sample_data():
    files = glob.glob(os.path.join(ROOT_PATH, '**/*.txt'), recursive=True)
    all_data = []
    
    print(f"Sampling sur {len(files)} fichiers...")
    
    for f in files[:200]: # On prend juste les 200 premiers fichiers pour l'exemple
        try:
            with open(f, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) > 1:
                        # Ignorer la date
                        vals = [float(x) for x in parts[1:]]
                        if len(vals) > 50: # On garde que les séries assez longues
                            all_data.append(vals)
        except:
            continue
            
    return all_data[:SAMPLE_SIZE]

# 1. Chargement
raw_data = load_sample_data()
if not raw_data:
    print("Aucune donnée trouvée.")
    exit()

# On prend une série au hasard pour l'afficher
random_idx = np.random.randint(0, len(raw_data))
sample_series = raw_data[random_idx]

# 2. Analyse Statistique
flat_data = [item for sublist in raw_data for item in sublist]
max_val = np.max(flat_data)
mean_val = np.mean(flat_data)
median_val = np.median(flat_data)

print(f"--- STATISTIQUES ---")
print(f"Max absolu : {max_val}")
print(f"Moyenne    : {mean_val:.2f}")
print(f"Médiane    : {median_val:.2f}")
print(f"99ème percentile : {np.percentile(flat_data, 99):.2f}") 
# Le 99ème percentile est crucial : il montre la "vraie" valeur max hors bugs

# 3. Visualisation
plt.figure(figsize=(15, 10))

# Plot 1: Une journée brute
plt.subplot(2, 2, 1)
plt.plot(sample_series)
plt.title(f"Exemple de Série Temporelle Brute (Index {random_idx})")
plt.xlabel("Temps")
plt.ylabel("Trafic")

# Plot 2: Histogramme des valeurs brutes (Zoomé)
plt.subplot(2, 2, 2)
# On coupe à 99% pour ne pas que le graph soit écrasé par le max à 5 millions
limit = np.percentile(flat_data, 99)
sns.histplot([x for x in flat_data if x < limit], bins=50)
plt.title("Distribution des valeurs (99% des données)")

# Plot 3: Transformation Logarithmique (La solution proposée)
plt.subplot(2, 2, 3)
log_series = np.log1p(sample_series)
plt.plot(log_series, color='green')
plt.title("Même série avec Transformation Log (np.log1p)")

# Plot 4: Comparaison Quantization (Linéaire vs Log)
plt.subplot(2, 2, 4)
# Simulation de ce que le script faisait avant (Linéaire)
vocab = 100
linear_quant = [int(x / max_val * vocab) for x in sample_series]
# Simulation de la nouvelle méthode (Log)
max_log = np.log1p(max_val)
log_quant = [int(np.log1p(x) / max_log * vocab) for x in sample_series]

plt.plot(linear_quant, label="Linéaire (Ancien script)", alpha=0.5)
plt.plot(log_quant, label="Logarithmique (Nouveau script)", color='red')
plt.legend()
plt.title("Simulation de la Quantization (0-100)")

plt.tight_layout()
plt.show()