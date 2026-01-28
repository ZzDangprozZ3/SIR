import os
import sys
import subprocess

# Configuration
DATA_DIR_NAME = "NetMob23"  # Nom du dossier contenant le dataset
ENTRYPOINT_SCRIPT = "pipeline.sh"

def check_data_presence(data_path):
    """Vérification de la présence des données dans le dossier spécifié"""
    if not os.path.exists(data_path):
        print(f"\nERREUR : Le dossier de données est introuvable !")
        print(f"Attendu ici : {data_path}")
        print(">>> ACTION REQUISE : Créez ce dossier et placez-y vos données NetMob (fichiers .txt).")
        return False
    
    if not os.listdir(data_path):
        print(f"\nATTENTION: Le dossier '{DATA_DIR_NAME}' existe mais est VIDE.")
        print(">>> aucune donnée à traiter")
        return False
        
    return True

def image_exists(image_name):
    try:
        output = subprocess.check_output(f"docker images -q {image_name}", shell=True)
        return len(output.strip()) > 0
    except subprocess.CalledProcessError:
        return False

def run_framework(framework_name, force_rebuild=False):
    root_dir = os.getcwd()
    framework_dir = os.path.join(root_dir, framework_name)
    data_dir = os.path.join(root_dir, DATA_DIR_NAME)
    fw_lower = framework_name.lower()
    
    if not os.path.isdir(framework_dir):
        print(f"ERREUR: Le dossier du framework '{framework_name}' n'existe pas.")
        return
    
    if not check_data_presence(data_dir):
        return 
    
    # =========================================================================
    # CAS SPÉCIAL : AlertRCA (via docker-compose)
    # =========================================================================
    if fw_lower == "alertrca":
        print(f"\n>>> Lancement de AlertRCA via Docker-Compose...")
        subprocess.call("docker-compose run --rm --build app", shell=True, cwd=framework_dir)
        print(f"\nFIN {framework_name.upper()}")
        return
    
    # =========================================================================
    # CAS SPÉCIAL : TraceAnomaly (via script Python)
    # =========================================================================
    if fw_lower == "traceanomaly":
        print(f"\n>>> Lancement de TraceAnomaly via script Python...")
        subprocess.call(f"{sys.executable} main.py", shell=True, cwd=framework_dir)
        print(f"\nFIN {framework_name.upper()}")
        return
    
    # =========================================================================
    # CAS SPÉCIAL : AOC_IDS (via run_complete_pipeline.sh)
    # =========================================================================
    if fw_lower == "aoc_ids":
        print(f"\n>>> Lancement de AOC_IDS via Pipeline Automatisé...")
        print("=" * 80)
        print("FRAMEWORK: AOC-IDS (Anomaly-based Online Continual Intrusion Detection)")
        print("PIPELINE : Conversion + Entraînement + Validation")
        print("DURÉE ESTIMÉE : 2-4 heures")
        print("=" * 80)
        
        # Vérifier que le script pipeline existe
        pipeline_script = os.path.join(framework_dir, "run_complete_pipeline.sh")
        if not os.path.exists(pipeline_script):
            print(f"\nERREUR: Le script 'run_complete_pipeline.sh' n'existe pas dans {framework_dir}")
            return
        
        # Vérifier que le dataset NetMob23 est dans le bon endroit
        aoc_data_dir = os.path.join(framework_dir, "Dataset NetMob23")
        
        # Si le dataset n'est pas dans AOC_IDS, créer un lien symbolique
        if not os.path.exists(aoc_data_dir):
            print(f"\n[INFO] Création d'un lien symbolique vers {DATA_DIR_NAME}...")
            try:
                os.symlink(data_dir, aoc_data_dir)
                print(f"[OK] Lien créé: {aoc_data_dir} -> {data_dir}")
            except Exception as e:
                print(f"[ERREUR] Impossible de créer le lien symbolique: {e}")
                print(f"[INFO] Tentative de copie du dataset...")
                subprocess.call(f'cp -r "{data_dir}" "{aoc_data_dir}"', shell=True)
        
        # Rendre le script exécutable
        subprocess.call(f"chmod +x {pipeline_script}", shell=True)
        
        # Lancer le pipeline complet
        print(f"\n[INFO] Lancement du pipeline AOC_IDS...")
        result = subprocess.call(f"bash run_complete_pipeline.sh", shell=True, cwd=framework_dir)
        
        if result == 0:
            print(f"\n{'=' * 80}")
            print(f" FIN {framework_name.upper()} - Pipeline terminé avec succès")
            print(f"{'=' * 80}")
            print(f"\n RÉSULTATS DISPONIBLES DANS:")
            print(f"   - {os.path.join(framework_dir, 'output', 'Facebook', 'validation_report.txt')}")
            print(f"   - {os.path.join(framework_dir, 'output', 'Netflix', 'validation_report.txt')}")
        else:
            print(f"\n ERREUR lors de l'exécution du pipeline AOC_IDS")
        
        return
    
    # =========================================================================
    # CAS GÉNÉRAL : Autres frameworks (AWSCTD, CausalRCA, SGmVRNN)
    # =========================================================================
    image_name = f"{fw_lower}_img"
    
    should_build = force_rebuild or not image_exists(image_name)
    if should_build:
        print(f"\n 1/3 Construction de l'image Docker ({image_name})...")
        build_cmd = f"docker build -t {image_name} ./{framework_name}"
        if subprocess.call(build_cmd, shell=True) != 0:
            print(" ERREUR : Le build a échoué.")
            return
    else:
        print(f"\n 1/3 Image {image_name} déjà présente (Cache)")
    
    print(f"🚀 2/3 Démarrage du pipeline...")
    
    data_dir_clean = data_dir.replace('\\', '/')
    framework_dir_clean = framework_dir.replace('\\', '/')
    
    docker_cmd = (
        f"docker run --rm "
        f"-v \"{data_dir_clean}:/data\" "
        f"-v \"{framework_dir_clean}:/app\" "
        f"{image_name} "
        f"bash {ENTRYPOINT_SCRIPT}"
    )
    
    subprocess.call(docker_cmd, shell=True)
    print(f"\n FIN {framework_name.upper()} ")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 80)
        print("USAGE: python main.py <nom_du_framework> [--rebuild]")
        print("=" * 80)
        print("\nFrameworks disponibles:")
        print("  - AWSCTD")
        print("  - AlertRCA")
        print("  - CausalRCA")
        print("  - SGmVRNN")
        print("  - TraceAnomaly")
        print("  - AOC_IDS        ← NOUVEAU")
        print("\nExemples:")
        print("  python main.py AWSCTD")
        print("  python main.py AOC_IDS")
        print("  python main.py AOC_IDS --rebuild")
        print("=" * 80)
    else:
        fw = sys.argv[1]
        rebuild = "--rebuild" in sys.argv
        run_framework(fw, force_rebuild=rebuild)
