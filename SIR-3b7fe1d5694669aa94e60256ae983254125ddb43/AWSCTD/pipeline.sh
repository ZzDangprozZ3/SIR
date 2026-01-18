#!/bin/bash

# Arrêter le script si une commande échoue
set -e 

echo ">>> Conversion des données NetMob..."
python3 convert_netmob_awsctd.py

echo ">>> Lecture de la configuration..."
MODEL_INFO=$(python3 -c "import configparser; c=configparser.ConfigParser(); c.read('config.ini'); print(c.get('MAIN', 'sModelName', fallback='AWSCTD-CNN-S') + '|' + c.get('FILES', 'sOutputCSV', fallback='netmob_for_awsctd.csv'))")

MODEL_NAME=$(echo $MODEL_INFO | cut -d'|' -f1)
CSV_NAME=$(echo $MODEL_INFO | cut -d'|' -f2)

echo ">>> Modèle : $MODEL_NAME | Fichier Data : $CSV_NAME"

echo ">>> Entraînement et Détection..."
python3 AWSCTD.py "$CSV_NAME" "$MODEL_NAME"

echo ">>> Terminé."