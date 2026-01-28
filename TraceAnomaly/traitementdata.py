import os
import glob

# On se situe dans TraceAnomaly/, donc on remonte d'un cran pour trouver NetMob23
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NETMOB_DIR = os.path.join(BASE_DIR, "..", "NetMob23")
OUTPUT_FILE = os.path.join(os.getcwd(), "merged_flows")

print(f"--- DÉBUT TRAITEMENT DATA ---")
print(f"Recherche des données dans : {os.path.abspath(NETMOB_DIR)}")

# Vérification que le dossier existe
if not os.path.exists(NETMOB_DIR):
    print(f"ERREUR CRITIQUE: Le dossier {NETMOB_DIR} n'existe pas.")
    exit(1)

# Recherche récursive de TOUS les fichiers .txt dans NetMob23 (peu importe le sous-dossier)
search_pattern = os.path.join(NETMOB_DIR, "**", "*.txt")
files = glob.glob(search_pattern, recursive=True)

print(f"Fichiers .txt trouvés : {len(files)}")

if len(files) == 0:
    print("ERREUR: Aucun fichier de données trouvé. Vérifiez que NetMob23 n'est pas vide.")
    # On ne quitte pas forcément ici pour laisser voir le fichier vide, mais c'est l'échec assuré
else:
    print(f"Exemple de fichier trouvé : {files[0]}")

count_lines = 0

with open(OUTPUT_FILE, "w", encoding="utf-8") as fout:
    for input_path in files:
        filename = os.path.basename(input_path)
        
        # Ignorer les fichiers qui ne sont pas du trafic (ex: anomalies.txt, reports, etc.)
        if "anomal" in filename.lower() or "report" in filename.lower() or "geojson" in filename.lower():
            continue

        try:
            # Logique d'extraction (basée sur ton code original)
            # Attention : cela suppose que le nom est formaté type "App_Region_Date.txt"
            # Si le nom est juste "tile_42.txt", il faudra adapter cette partie.
            parts_name = os.path.splitext(filename)[0].split("_")
            
            # Sécurité si le nom du fichier est court
            if len(parts_name) >= 2:
                application = parts_name[0]
                region_id = parts_name[-1]
            else:
                application = "Unknown"
                region_id = parts_name[0]

            with open(input_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 2:
                        continue
                    
                    date = parts[0]
                    # Nettoyage des 'nan'
                    vals = ['0' if x.lower() == 'nan' else x for x in parts[1:]]
                    
                    # Construction de l'ID unique
                    flow_id = f"{application}_{region_id}_{date}"
                    
                    # Format attendu par TraceAnomaly: ID:val1,val2,val3
                    formatted = flow_id + ":" + ",".join(vals)
                    fout.write(formatted + "\n")
                    count_lines += 1
        except Exception as e:
            print(f"Erreur sur le fichier {filename}: {e}")

print(f"Conversion terminée.")
print(f"Lignes écrites dans merged_flows : {count_lines}")
print(f"Fichier généré : {OUTPUT_FILE}")
print(f"--- FIN TRAITEMENT DATA ---")