#!/bin/bash

# Arrêter le script si une commande échoue
set -e 

echo ">>> Conversion des données NetMob..."
# On lit depuis /data (le volume NetMob23 monté)
python3 convert_netmob_awsctd.py

echo ">>> Entraînement et Détection..."
# Le CSV est généré dans le dossier courant
python3 AWSCTD.py netmob_for_awsctd.csv AWSCTD-CNN-S

echo ">>> Terminé."