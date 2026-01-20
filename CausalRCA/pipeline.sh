#!/bin/bash

# Configuration
get_config() {
    python -c "import configparser; c=configparser.ConfigParser(); c.read('config.ini'); val=c.get('$1', '$2', fallback='$3'); print(val.lower())"
}

echo "   STARTING CAUSAL RCA PIPELINE    "

ANOMALY_FILENAME=$(get_config 'PATHS' 'anomalies_file' 'ANOMALY_REPORT.txt')
ANOMALY_FILE="/data/$ANOMALY_FILENAME"
DATA_DIR="./data_collected"

FORCE_CLEAN=$(get_config 'PIPELINE' 'force_clean' 'true')

if [ "$FORCE_CLEAN" = "true" ]; then
    echo ">>> Mode nettoyage activé (via config.ini)."
    echo "    Suppression des anciens fichiers .pkl, .json et .png..."
    rm -f $DATA_DIR/anomaly_*.pkl
    rm -f $DATA_DIR/anomaly_*.json
    rm -f $DATA_DIR/anomaly_*.png
    echo "    Dossier nettoyé."
else
    echo ">>> Mode reprise (force_clean=false)."
    echo "    Les fichiers existants ne seront pas effacés."
fi

# Génération des Datasets (Si nécessaire)
count_pkl=$(ls $DATA_DIR/anomaly_*.pkl 2>/dev/null | wc -l)

if [ "$count_pkl" -gt 0 ]; then
    echo ">>> $count_pkl datasets détectés."
    echo ">>> On saute l'étape de génération."
else
    echo ">>> Aucun dataset trouvé. Lancement de la conversion..."
    if [ -f "$ANOMALY_FILE" ]; then
        python convert_netmob_causalrca.py --anomalies_file "$ANOMALY_FILE"
    else
        echo "ERREUR CRITIQUE: Fichier d'anomalies introuvable : $ANOMALY_FILE"
        exit 1
    fi
fi

ETA=$(get_config 'TRAINING' 'eta' '2')
GAMMA=$(get_config 'TRAINING' 'gamma' '0.25')
EPOCHS=$(get_config 'TRAINING' 'epochs' '200')

# Boucle d'entraînement
echo ">>> Démarrage de l'analyse CausalRCA..."
echo "    Paramètres : Eta=$ETA, Gamma=$GAMMA, Epochs=$EPOCHS"

count=0
for pkl_file in $DATA_DIR/anomaly_*.pkl; do
    [ -e "$pkl_file" ] || continue 
    
    echo "------------------------------------------------"
    echo "Traitement de : $(basename "$pkl_file")"
    
    python train_all_services.py \
        --data_file "$pkl_file" \
        --epochs $EPOCHS \
        --eta $ETA \
        --gamma $GAMMA
        
    ((count++))
done

# Agrégation finale
echo ">>> Agrégation des résultats..."
python -c "
import glob, json, pandas as pd, os
results = []
for f in glob.glob('./data_collected/*_result.json'):
    try:
        with open(f, 'r') as json_file:
            data = json.load(json_file)
            if data.get('pagerank_scores'):
                top_cause = data['pagerank_scores'][0] 
                cause_idx = top_cause[0]
                score = top_cause[1]
            else:
                cause_idx, score = 'Inconnu', 0
            
            filename = os.path.basename(f)
            parts = filename.replace('_result.json', '').split('_')
            
            results.append({
                'Fichier_Source': filename,
                'Date_Anomalie': parts[1] if len(parts)>1 else '?',
                'Tuile_Cible': parts[2] if len(parts)>2 else '?',
                'Cause_Racine_Detectee': cause_idx,
                'Score_PageRank': score
            })
    except: pass

if results:
    df = pd.DataFrame(results)
    try:
        df = df.sort_values(by='Date_Anomalie')
    except: pass
    output_csv = '/data/GLOBAL_RCA_RESULTS.csv'
    df.to_csv(output_csv, index=False)
    print(f'   [SUCCESS] Rapport global généré : {output_csv} ({len(df)} lignes)')
else:
    print('   [INFO] Aucun résultat à agréger.')
"


echo "   PIPELINE TERMINÉ ($count cas traités)"
