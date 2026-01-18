#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'exploration du dataset NetMob23
Auteur: Fadwa
Date: Décembre 2024
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
import json

# ========================================
# PARTIE 1 : CONFIGURATION
# ========================================

# ⚠️ MODIFIE CE CHEMIN AVEC TON CHEMIN RÉEL
BASE_PATH = "/home/lenovo-loq/Bureau/Dataset NetMob23"  

# Créer un dossier pour les résultats
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


# ========================================
# PARTIE 2 : FONCTIONS D'ANALYSE
# ========================================

def read_netmob_file(filepath):
    """
    Lit un fichier NetMob23 et retourne ses informations
    
    Args:
        filepath: Chemin vers le fichier .txt
        
    Returns:
        dict: Informations sur le fichier
    """
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Première ligne = date
        date = lines[0].strip()
        
        # Lignes suivantes = valeurs
        values = []
        for line in lines[1:]:
            # Séparer par espaces et convertir en float
            line_values = line.strip().split()
            for val in line_values:
                if val:  # Ignorer les chaînes vides
                    try:
                        values.append(float(val))
                    except ValueError:
                        # Ignorer les valeurs non-numériques (comme 'nan')
                        continue
        
        # Calculer des statistiques (en filtrant les NaN)
        values_array = np.array(values)
        values_array = values_array[~np.isnan(values_array)]  # Retirer les NaN
        
        if len(values_array) == 0:
            return None
        
        return {
            'filename': filepath.name,
            'date': date,
            'n_values': len(values),
            'min': float(values_array.min()),
            'max': float(values_array.max()),
            'mean': float(values_array.mean()),
            'std': float(values_array.std()),
            'median': float(np.median(values_array)),
            'has_zeros': int(np.sum(values_array == 0)),
            'has_nans': int(len(values) - len(values_array)),
            'values_sample': values[:5]  # 5 premières valeurs
        }
    
    except Exception as e:
        print(f"❌ Erreur en lisant {filepath.name}: {e}")
        return None


def explore_application(app_name, base_path, n_files=10):
    """
    Explore les fichiers d'une application (Facebook, Netflix, Spotify)
    
    Args:
        app_name: Nom de l'application
        base_path: Chemin de base du dataset
        n_files: Nombre de fichiers à analyser
        
    Returns:
        list: Liste des résultats d'analyse
    """
    print(f"\n{'='*60}")
    print(f"📱 Analyse de {app_name}")
    print(f"{'='*60}")
    
    # Chemin vers le dossier DL de l'application
    dl_path = Path(base_path) / app_name / 'DL'
    
    if not dl_path.exists():
        print(f"❌ Le dossier {dl_path} n'existe pas !")
        return []
    
    # Liste tous les fichiers .txt
    all_files = list(dl_path.glob('*.txt'))
    total_files = len(all_files)
    
    print(f"📊 Nombre total de fichiers : {total_files}")
    
    if total_files == 0:
        print("❌ Aucun fichier .txt trouvé !")
        return []
    
    # Sélectionner n_files fichiers
    files_to_analyze = all_files[:n_files]
    
    print(f"🔍 Analyse de {len(files_to_analyze)} fichiers...")
    print()
    
    results = []
    
    for i, filepath in enumerate(files_to_analyze, 1):
        print(f"   [{i}/{len(files_to_analyze)}] {filepath.name}... ", end='')
        
        info = read_netmob_file(filepath)
        
        if info:
            results.append(info)
            print(f"✓ ({info['n_values']} valeurs, moy={info['mean']:.2f})")
        else:
            print("✗")
    
    return results


def print_summary(results, app_name):
    """
    Affiche un résumé des résultats
    
    Args:
        results: Liste des résultats d'analyse
        app_name: Nom de l'application
    """
    if not results:
        print(f"\n⚠️  Aucun résultat pour {app_name}")
        return
    
    print(f"\n📈 Résumé pour {app_name}:")
    print(f"   • Fichiers analysés : {len(results)}")
    
    # Statistiques globales
    all_means = [r['mean'] for r in results]
    all_maxs = [r['max'] for r in results]
    all_n_values = [r['n_values'] for r in results]
    
    print(f"   • Valeurs par fichier : {all_n_values[0]} (devrait être 96)")
    print(f"   • Moyenne globale : {np.mean(all_means):.2f}")
    print(f"   • Max global : {max(all_maxs):.2f}")
    
    # Dates
    dates = [r['date'] for r in results]
    print(f"   • Première date : {min(dates)}")
    print(f"   • Dernière date : {max(dates)}")


def save_results(all_results, output_file="results/exploration_results.json"):
    """
    Sauvegarde les résultats dans un fichier JSON
    
    Args:
        all_results: Dictionnaire avec les résultats par application
        output_file: Chemin du fichier de sortie
    """
    output_path = Path(output_file)
    
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n💾 Résultats sauvegardés dans : {output_path}")


# ========================================
# PARTIE 3 : FONCTION PRINCIPALE
# ========================================

def main():
    """
    Fonction principale qui orchestre l'exploration
    """
    print("\n" + "="*60)
    print("🚀 EXPLORATION DU DATASET NETMOB23")
    print("="*60)
    
    # Vérifier que le chemin de base existe
    if not Path(BASE_PATH).exists():
        print(f"\n❌ ERREUR : Le chemin {BASE_PATH} n'existe pas !")
        print("   👉 Modifie la variable BASE_PATH dans le script")
        return
    
    print(f"\n📂 Chemin du dataset : {BASE_PATH}")
    
    # Explorer chaque application
    all_results = {}
    
    for app_name in ['Facebook', 'Netflix', 'Spotify']:
        results = explore_application(app_name, BASE_PATH, n_files=10)
        all_results[app_name] = results
        print_summary(results, app_name)
    
    # Sauvegarder les résultats
    save_results(all_results)
    
    print("\n" + "="*60)
    print("✅ EXPLORATION TERMINÉE !")
    print("="*60)
    print("\n📝 Prochaines étapes :")
    print("   1. Vérifie le fichier results/exploration_results.json")
    print("   2. Partage ces résultats avec ton groupe Discord")
    print("   3. Passe à l'étape 1.2 : Documentation\n")


# ========================================
# POINT D'ENTRÉE DU SCRIPT
# ========================================

if __name__ == "__main__":
    main()