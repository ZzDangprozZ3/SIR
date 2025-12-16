#!/bin/bash

# Arrêter le script si une commande échoue
set -e 

echo ">>> Conversion des données NetMob..."

python3 convert_netmob_awsctd.py

echo ">>> Entraînement et Détection..."

python3 AWSCTD.py netmob_for_awsctd.csv AWSCTD-CNN-S

echo ">>> Terminé."