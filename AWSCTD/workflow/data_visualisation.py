import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import os
import sys
import numpy as np

#CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemins
TXT_DIR_PATH = os.path.abspath(os.path.join(BASE_DIR, '../../netmob23/'))
CSV_FILE_PATH = os.path.join(BASE_DIR, 'netmob_for_awsctd.csv') 

def get_user_choice():
    print("\n--- MENU VISUALISATION ---")
    print(f"1. Données BRUTES (.txt) -> {TXT_DIR_PATH}")
    print(f"2. Dataset PROCESSÉ (.csv) -> {CSV_FILE_PATH}")
    print("3. Quitter")
    return input("\nChoix : ").strip()

def load_txt_data():
    print(f"\n Recherche .txt dans {TXT_DIR_PATH}...")
    files = glob.glob(os.path.join(TXT_DIR_PATH, '**/*.txt'), recursive=True)
    
    if not files:
        print(" Erreur : Aucun fichier .txt trouvé.")
        return None

    # Limite pour éviter d'attendre trop longtemps pendant le test
    MAX_FILES_TEST = 10000
    if len(files) > MAX_FILES_TEST:
        print(f"  Mode Test : Chargement des {MAX_FILES_TEST} premiers fichiers seulement.")
        files = files[:MAX_FILES_TEST]

    aggregated_df = None
    print(f" Fusion de {len(files)} fichiers...")

    for i, file in enumerate(files):
        try:
            # Lecture flexible (sépare par espace ou tabulation)
            df_temp = pd.read_csv(file, sep=r'\s+', header=None, engine='python')
            
            # On suppose: Col 0 = Date (YYYYMMDD), Col 1+ = Trafic
            df_temp.rename(columns={0: 'Date'}, inplace=True)
            df_temp['Date'] = df_temp['Date'].astype(str)
            
            # Agrégation par date
            df_grouped = df_temp.groupby('Date').sum()

            if aggregated_df is None:
                aggregated_df = df_grouped
            else:
                aggregated_df = aggregated_df.add(df_grouped, fill_value=0)
                
        except Exception:
            pass # On ignore les fichiers illisibles

    print(f" Terminé. Forme : {aggregated_df.shape}")
    return aggregated_df

def load_csv_data():
    """Version robustifiée pour le CSV"""
    print(f"\n Lecture du CSV : {CSV_FILE_PATH}")
    
    if not os.path.exists(CSV_FILE_PATH):
        print(f" ERREUR : Fichier introuvable !\nVérifiez le chemin : {CSV_FILE_PATH}")
        return None
        
    try:
        # 1. Tentative de lecture standard (Virgule)
        df = pd.read_csv(CSV_FILE_PATH, header=None)
        
        # 2. Vérification si le séparateur était mauvais (ex: tout est dans 1 seule colonne)
        if df.shape[1] < 2:
            print("  Attention : 1 seule colonne détectée. Tentative avec séparateur 'espace'...")
            df = pd.read_csv(CSV_FILE_PATH, header=None, sep=r'\s+', engine='python')

        # 3. Vérification du contenu (DEBUG)
        print(f" Info Dataset : {df.shape[0]} lignes, {df.shape[1]} colonnes")
        print("   Aperçu des données :")
        print(df.iloc[:2, :5]) # Affiche les 2 premières lignes, 5 premières colonnes
        
        # 4. Conversion forcée en numérique (au cas où il y a des strings)
        # On essaie de convertir, si erreur -> NaN -> 0
        df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
        
        return df

    except Exception as e:
        print(f" Erreur critique lors de la lecture du CSV : {e}")
        return None

def plot_heatmap(df, title, is_txt=True):
    print(" Génération du graphique...")
    plt.figure(figsize=(16, 9))
    
    if is_txt:
        # CAS 1 : TXT 
        df.sort_index(inplace=True)
        # Formatage dates pour axe Y
        labels = [d if len(str(d))!=8 else f"{str(d)[:4]}-{str(d)[4:6]}-{str(d)[6:]}" for d in df.index]
        
        # Axe Y allégé (1 date tous les 7 jours)
        step = max(1, len(df)//20) 
        
        ax = sns.heatmap(df, cmap='inferno', robust=True, cbar_kws={'label': 'Volume Trafic'})
        
        # Application labels
        ax.set_yticks(np.arange(0, len(df), step) + 0.5)
        ax.set_yticklabels([labels[i] for i in range(0, len(df), step)], rotation=0)
        
        plt.xlabel("Temps (Quarts d'heure)")
        plt.ylabel("Date")

    else:
        #  CAS 2 : CSV 
        # Limitation pour éviter le crash mémoire
        limit_rows = 10000
        
        if len(df) > limit_rows:
            print(f" Affichage limité aux {limit_rows} premières séquences pour lisibilité.")
            df_viz = df.iloc[:limit_rows, :-1] # On retire la dernière colonne (Label)
        else:
            df_viz = df.iloc[:, :-1]

        # Vérification finale avant plot
        if df_viz.shape[1] == 0:
            print(" Erreur : Pas de données à afficher (DataFrame vide après découpage).")
            return

        ax = sns.heatmap(df_viz, cmap='viridis', robust=True, cbar_kws={'label': 'Niveau (0-100)'})
        plt.xlabel("Pas de temps (Index dans la séquence)")
        plt.ylabel("Index de l'échantillon")

    plt.title(title)
    plt.tight_layout()
    
    # Sauvegarde automatique au cas où l'affichage plante
    out_file = "debug_heatmap.png"
    plt.savefig(out_file)
    print(f" Image sauvegardée sous : {out_file}")
    plt.show()

# MAIN
if __name__ == "__main__":
    while True:
        c = get_user_choice()
        if c == '1':
            d = load_txt_data()
            if d is not None: plot_heatmap(d, "NetMob23 Brutes (Vue Calendrier)", True)
        elif c == '2':
            d = load_csv_data()
            if d is not None: plot_heatmap(d, "Dataset Processé AWSCTD (Vue Séquences)", False)
        elif c == '3':
            break
        else:
            print("Choix invalide.")