#!/bin/bash

# Fonction utilitaire pour lire le config.ini via Python
get_config() {
    python -c "import configparser; c=configparser.ConfigParser(); c.read('config.ini'); print(c.get('$1', '$2'))"
}

echo "   STARTING CAUSAL RCA PIPELINE    "

# Conversion des données
if [ -f "convert_netmob_causalrca.py" ]; then
    echo ">>> 1/3 Conversion des données NetMob..."
    python convert_netmob_causalrca.py
else
    echo "ERREUR: convert_netmob_causalrca.py introuvable !"
    exit 1
fi

# Adaptation dynamique du code Python
echo ">>> 2/3 Configuration du script d'entraînement..."

SVC_NAME=$(get_config 'PATHS' 'service_name')
PREFIX=$(get_config 'PATHS' 'output_prefix')

TARGET_SCRIPT="train_all_services.py"

sed -i "s/^names = .*/names = ['$SVC_NAME']/" $TARGET_SCRIPT
echo ">>> Variable 'names' remplacée par ['$SVC_NAME']"

# Lancement de l'entraînement
echo ">>> 3/3 Lancement de l'entraînement CausalRCA..."

# Récupération des hyperparamètres
INDX=$(get_config 'TRAINING' 'service_index')
ETA=$(get_config 'TRAINING' 'eta')
GAMMA=$(get_config 'TRAINING' 'gamma')

echo ">>> Paramètres: Index=$INDX, Prefix=$PREFIX, Eta=$ETA, Gamma=$GAMMA"

python $TARGET_SCRIPT --indx $INDX --atype "$PREFIX" --eta $ETA --gamma $GAMMA


echo "   PIPELINE TERMINÉ. "