#!/bin/bash

# Configuration
ANOMALY_FILE="/data/netmob_for_awsctd.csv" # Nom du fichier dans le volume monté

echo "   STARTING CAUSAL RCA PIPELINE    "

# 1. Conversion en Batch
if [ -f "$ANOMALY_FILE" ]; then
    echo ">>> 1/2 Génération des datasets pour chaque anomalie..."
    # On passe le fichier d'anomalies au script Python
    python convert_netmob_causalrca.py --anomalies_file "$ANOMALY_FILE"
else
    echo "ERREUR: Fichier d'anomalies introuvable dans $ANOMALY_FILE"
    exit 1
fi

# 2. Boucle d'entraînement sur les fichiers générés
echo ">>> 2/2 Analyse CausalRCA pour chaque dataset..."

# On cherche tous les fichiers qui commencent par "anomaly_" dans data_collected
for pkl_file in ./data_collected/anomaly_*.pkl; do
    [ -e "$pkl_file" ] || continue # Si aucun fichier trouvé
    
    echo "------------------------------------------------"
    echo "Traitement de : $pkl_file"
    
    # On lance l'entraînement en lui passant le fichier spécifique
    # Plus besoin de 'sed', on utilise l'argument propre --data_file
    python train_all_services.py \
        --data_file "$pkl_file" \
        --epochs 10 \
        --eta 10 \
        --gamma 0.25
        
done

echo "   BATCH PROCESSING TERMINÉ."