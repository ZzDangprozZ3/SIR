#!/bin/bash

################################################################################
# PIPELINE COMPLET - AOC-IDS ADAPTATION NETMOB23
################################################################################
# 
# Ce script exécute l'intégralité du pipeline d'adaptation d'AOC-IDS
# pour le dataset NetMob23 (Facebook et Netflix)
#
# PRÉREQUIS:
#   - Docker installé
#   - Dataset NetMob23 dans le dossier: ./Dataset NetMob23/
#
# USAGE:
#   bash run_complete_pipeline.sh
#
# DURÉE ESTIMÉE: 2-4 heures (selon votre machine)
#
################################################################################

set -e  # Arrêter le script en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║        AOC-IDS ADAPTATION POUR NETMOB23                        ║${NC}"
echo -e "${BLUE}║        Pipeline Complet d'Exécution                            ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERREUR]${NC} Docker n'est pas installé!"
    echo "Installez Docker: https://www.docker.com/get-started"
    exit 1
fi

# Vérifier que le dataset existe
if [ ! -d "Dataset NetMob23" ]; then
    echo -e "${RED}[ERREUR]${NC} Dossier 'Dataset NetMob23' introuvable!"
    echo "Placez le dataset NetMob23 dans ce dossier."
    exit 1
fi

# Créer le dossier de sortie
mkdir -p output

echo -e "${YELLOW}[INFO]${NC} Démarrage du pipeline..."
echo ""

################################################################################
# ÉTAPE 1 : CONSTRUCTION DE L'IMAGE DOCKER
################################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}ÉTAPE 1/7 : Construction de l'image Docker${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

docker build -t aoc-ids-netmob .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Image Docker construite avec succès"
else
    echo -e "${RED}✗${NC} Erreur lors de la construction de l'image"
    exit 1
fi

echo ""

################################################################################
# ÉTAPE 2 : CONVERSION DES DONNÉES NETMOB23
################################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}ÉTAPE 2/7 : Conversion des données NetMob23${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}[INFO]${NC} Extraction des 15 features + Pseudo-labelling..."
echo ""

docker run --rm \
    -v "$(pwd)/Dataset NetMob23":/data/input:ro \
    -v "$(pwd)/output":/data/output \
    aoc-ids-netmob \
    python convert.py \
    --input /data/input \
    --output /data/output \
    --contamination 0.05

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Conversion terminée"
else
    echo -e "${RED}✗${NC} Erreur lors de la conversion"
    exit 1
fi

echo ""

################################################################################
# ÉTAPE 3 : ENTRAÎNEMENT AOC-IDS - FACEBOOK
################################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}ÉTAPE 3/7 : Entraînement AOC-IDS - Facebook${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}[INFO]${NC} Entraînement du modèle sur Facebook (50 epochs)..."
echo ""

docker run --rm \
    -v "$(pwd)/output":/data/output \
    aoc-ids-netmob \
    python AOC_IDS_FINI.py --dataset netmob \
    --train_path /data/output/Facebook/FacebookTrain.csv \
    --test_path /data/output/Facebook/FacebookTest.csv \
    --epochs 50 \
    --output_path /data/output/Facebook/anomalies_detected.csv

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Entraînement Facebook terminé"
else
    echo -e "${RED}✗${NC} Erreur lors de l'entraînement Facebook"
    exit 1
fi

echo ""

################################################################################
# ÉTAPE 4 : VALIDATION CROISÉE - FACEBOOK
################################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}ÉTAPE 4/7 : Validation croisée - Facebook${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

docker run --rm \
    -v "$(pwd)/output":/data/output \
    aoc-ids-netmob \
    python validation.py \
    --data_path /data/output/Facebook/FacebookTest.csv \
    --aoc_predictions /data/output/Facebook/anomalies_detected_all.csv \
    --service Facebook \
    --output_report /data/output/Facebook/validation_report.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Validation Facebook terminée"
else
    echo -e "${YELLOW}⚠${NC}  Validation Facebook échouée (peut-être que anomalies_detected_all.csv n'existe pas)"
fi

echo ""

################################################################################
# ÉTAPE 5 : ENTRAÎNEMENT AOC-IDS - NETFLIX
################################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}ÉTAPE 5/7 : Entraînement AOC-IDS - Netflix${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}[INFO]${NC} Entraînement du modèle sur Netflix (50 epochs)..."
echo ""

docker run --rm \
    -v "$(pwd)/output":/data/output \
    aoc-ids-netmob \
    python AOC_IDS_FINI.py --dataset netmob \
    --train_path /data/output/Netflix/NetflixTrain.csv \
    --test_path /data/output/Netflix/NetflixTest.csv \
    --epochs 50 \
    --output_path /data/output/Netflix/anomalies_detected.csv

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Entraînement Netflix terminé"
else
    echo -e "${RED}✗${NC} Erreur lors de l'entraînement Netflix"
    exit 1
fi

echo ""

################################################################################
# ÉTAPE 6 : VALIDATION CROISÉE - NETFLIX
################################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}ÉTAPE 6/7 : Validation croisée - Netflix${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

docker run --rm \
    -v "$(pwd)/output":/data/output \
    aoc-ids-netmob \
    python validation.py \
    --data_path /data/output/Netflix/NetflixTest.csv \
    --aoc_predictions /data/output/Netflix/anomalies_detected_all.csv \
    --service Netflix \
    --output_report /data/output/Netflix/validation_report.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Validation Netflix terminée"
else
    echo -e "${YELLOW}⚠${NC}  Validation Netflix échouée (peut-être que anomalies_detected_all.csv n'existe pas)"
fi

echo ""

################################################################################
# ÉTAPE 7 : RÉSUMÉ DES RÉSULTATS
################################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}ÉTAPE 7/7 : Résumé des résultats${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}║                    PIPELINE TERMINÉ !                          ║${NC}"
echo -e "${GREEN}║                                                                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}📂 FICHIERS GÉNÉRÉS :${NC}"
echo ""
echo "  output/"
echo "  ├── Facebook/"
echo "  │   ├── FacebookTrain.csv"
echo "  │   ├── FacebookTest.csv"
echo "  │   ├── anomalies_detected.csv"
echo "  │   ├── anomalies_detected_all.csv (si généré)"
echo "  │   └── validation_report.txt"
echo "  └── Netflix/"
echo "      ├── NetflixTrain.csv"
echo "      ├── NetflixTest.csv"
echo "      ├── anomalies_detected.csv"
echo "      ├── anomalies_detected_all.csv (si généré)"
echo "      └── validation_report.txt"
echo ""

echo -e "${YELLOW}📊 CONSULTER LES RÉSULTATS :${NC}"
echo ""
echo "  - Validation Facebook : cat output/Facebook/validation_report.txt"
echo "  - Validation Netflix  : cat output/Netflix/validation_report.txt"
echo ""

echo -e "${GREEN}✓${NC} Pipeline d'adaptation AOC-IDS terminé avec succès !"
echo ""