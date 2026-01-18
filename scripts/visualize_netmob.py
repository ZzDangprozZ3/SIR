#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de visualisation du dataset NetMob23
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_results(filepath="results/exploration_results.json"):
    """Charge les résultats de l'exploration"""
    with open(filepath, 'r') as f:
        return json.load(f)

def plot_file_example(filepath, save_path="results/example_plot.png"):
    """
    Trace le graphique d'un fichier NetMob23
    
    Args:
        filepath: Chemin vers un fichier .txt
        save_path: Où sauvegarder le graphique
    """
    # Convertir en Path object si c'est un string
    filepath = Path(filepath)
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    date = lines[0].strip()
    values = []
    for line in lines[1:]:
        line_values = line.strip().split()
        values.extend([float(x) for x in line_values if x])
    
    # Créer le graphique
    plt.figure(figsize=(12, 6))
    plt.plot(values, linewidth=2, color='#2E86AB')
    plt.title(f'Trafic réseau - {filepath.name} - Date: {date}', fontsize=14, fontweight='bold')
    plt.xlabel('Intervalle de 15 minutes (0-95 = 24h)', fontsize=12)
    plt.ylabel('Volume de trafic', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Sauvegarder
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"📊 Graphique sauvegardé : {save_path}")
    plt.close()

def create_summary_table(results):
    """Crée un tableau résumé"""
    print("\n" + "="*70)
    print("📊 TABLEAU RÉCAPITULATIF")
    print("="*70)
    print(f"{'Application':<15} {'Fichiers':<10} {'Moy':<10} {'Max':<10} {'Valeurs':<10}")
    print("-"*70)
    
    for app_name, data in results.items():
        if not data:
            continue
            
        n_files = len(data)
        means = [d['mean'] for d in data]
        maxs = [d['max'] for d in data]
        n_values = data[0]['n_values']
        
        print(f"{app_name:<15} {n_files:<10} {np.mean(means):<10.2f} "
              f"{max(maxs):<10.2f} {n_values:<10}")
    
    print("="*70)

def main():
    """Fonction principale"""
    print("\n🎨 VISUALISATION DES RÉSULTATS NETMOB23\n")
    
    # Charger les résultats
    results = load_results()
    
    # Afficher le tableau récapitulatif
    create_summary_table(results)
    
    # Créer un graphique d'exemple (premier fichier Facebook)
    # ⚠️ MODIFIE CE CHEMIN
    example_file = "/home/lenovo-loq/Bureau/Dataset NetMob23/Facebook/DL/Facebook_DL_Tile_1510.txt"
    
    if Path(example_file).exists():
        plot_file_example(example_file)
    else:
        print(f"⚠️  Fichier exemple non trouvé : {example_file}")
    
    print("\n✅ Visualisation terminée !\n")

if __name__ == "__main__":
    main()