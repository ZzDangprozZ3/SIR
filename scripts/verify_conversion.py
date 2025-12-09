#!/usr/bin/env python3
"""
Vérification des fichiers convertis
"""

import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

def verify_file(filepath):
    """Vérifie un fichier converti"""
    try:
        data = np.loadtxt(filepath)
        
        print(f"\n✓ {filepath.name}")
        print(f"  Shape: {data.shape} (devrait être (96, 5))")
        print(f"  Timestamps: {data[0,0]:.0f} → {data[-1,0]:.0f}")
        print(f"  Traffic range: [{data[:,1].min():.0f}, {data[:,1].max():.0f}]")
        print(f"  NaN count: {np.isnan(data).sum()}")
        
        return True
    except Exception as e:
        print(f"\n✗ {filepath.name}: {e}")
        return False

def plot_example(filepath, save_path="../results/conversion_example.png"):
    """Trace un exemple de série convertie"""
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    data = np.loadtxt(filepath)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Exemple de conversion - {filepath.name}', fontsize=14, fontweight='bold')
    
    # Traffic brut
    axes[0,0].plot(data[:,1], linewidth=2, color='#2E86AB')
    axes[0,0].set_title('Traffic brut')
    axes[0,0].set_xlabel('Timestep (15 min)')
    axes[0,0].set_ylabel('Volume')
    axes[0,0].grid(True, alpha=0.3)
    
    # Rolling mean
    axes[0,1].plot(data[:,2], linewidth=2, color='#A23B72')
    axes[0,1].set_title('Moyenne mobile')
    axes[0,1].set_xlabel('Timestep')
    axes[0,1].set_ylabel('Moyenne')
    axes[0,1].grid(True, alpha=0.3)
    
    # Rolling std
    axes[1,0].plot(data[:,3], linewidth=2, color='#F18F01')
    axes[1,0].set_title('Écart-type mobile')
    axes[1,0].set_xlabel('Timestep')
    axes[1,0].set_ylabel('Std')
    axes[1,0].grid(True, alpha=0.3)
    
    # Diff
    axes[1,1].plot(data[:,4], linewidth=2, color='#C73E1D')
    axes[1,1].set_title('Différence première')
    axes[1,1].set_xlabel('Timestep')
    axes[1,1].set_ylabel('Variation')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\n📊 Graphique sauvegardé: {save_path}")
    plt.close()

def main():
    """Vérifie tous les fichiers convertis"""
    data_dir = Path("../data_converted")
    
    print("\n" + "="*70)
    print("🔍 VÉRIFICATION DES FICHIERS CONVERTIS")
    print("="*70)
    
    files = list(data_dir.glob("series_*.txt"))
    
    if not files:
        print("\n❌ Aucun fichier trouvé dans data_converted/")
        return
    
    print(f"\n✓ {len(files)} fichiers trouvés")
    
    # Vérifier les 5 premiers
    print("\n📋 Vérification des 5 premiers fichiers:")
    for f in files[:5]:
        verify_file(f)
    
    # Tracer un exemple
    print("\n📊 Création d'un graphique exemple...")
    plot_example(files[0])
    
    print("\n" + "="*70)
    print("✅ VÉRIFICATION TERMINÉE !")
    print("="*70)

if __name__ == "__main__":
    main()