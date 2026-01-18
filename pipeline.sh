#!/bin/bash

# Arrêter le script en cas d'erreur
set -e

echo "=== Exécution de traitementdata.py ==="
python traitementdata.py

echo "=== Lancement de docker compose ==="
docker compose run --rm --build traceanomaly

echo "=== Exécution de dectection.py ==="
python detection_anomaly.py

echo "=== Script terminé avec succès ==="
