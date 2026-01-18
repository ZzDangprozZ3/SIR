#!/bin/bash
set -e   # Arrêter le script si une commande échoue

# ---------------------------------------------------
# Étape 1 : Message d'information
# ---------------------------------------------------
echo ">>> Exécution de traitementdata.py pour le traitement des données..."

# ---------------------------------------------------
# Étape 2 : Exécution du script Python pour générer faults.csv, metrics, graph.yml,...
# ---------------------------------------------------
# Mettre à jour les chemins input_file et merged_flows_file dans traitementdata_1.py si nécessaire
python traitementdata.py

echo "✔ Étape traitementdata.py terminée"

# ---------------------------------------------------
# Étape 3 : Lancement de Docker Compose
# ---------------------------------------------------
echo ">>> Démarrage de Docker Compose..."
docker compose run --rm --build app


echo "✔ Docker Compose s’est exécuté avec succès"
