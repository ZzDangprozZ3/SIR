#!/bin/bash

echo "   STARTING CAUSAL RCA PIPELINE (NETMOB)   "

#Conversion des données
if [ -f "convert_netmob_causalrca.py" ]; then
    echo ">>> 1/3 Conversion des données NetMob..."
    python convert_netmob_causalrca.py
else
    echo "ERREUR: convert_netmob_causalrca.py introuvable !"
    exit 1
fi

# Adaptation dynamique du code Python
echo ">>> 2/3 Configuration du script d'entraînement..."

TARGET_SCRIPT="train_all_services.py"

# On utilise sed pour remplacer la définition de la liste 'names'
sed -i "s/^names = .*/names = ['top_tiles']/" $TARGET_SCRIPT

echo ">>> Code modifié : Variable 'names' mise à jour pour NetMob."

# Lancement de l'entraînement
echo ">>> 3/3 Lancement de l'entraînement CausalRCA..."
# --indx 0 : correspond à l'index de 'top_tiles' dans notre liste liste
# --atype "netmob_" : le préfixe défini dans le convertisseur
python $TARGET_SCRIPT --indx 0 --atype "netmob_" --eta 10


echo "   PIPELINE TERMINÉ. "
