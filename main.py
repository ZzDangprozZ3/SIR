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


    if not os.path.isdir(framework_dir):
        print(f"ERREUR: Le dossier du framework '{framework_name}' n'existe pas.")
        return

    if not check_data_presence(data_dir):
        return # On arrête tout si pas de data

    image_name = f"{framework_name.lower()}_img"
    
    # Build
    should_build = force_rebuild or not image_exists(image_name)
    if should_build:
        print(f"\n 1/3 Construction de l'image Docker ({image_name})...")
        build_cmd = f"docker build -t {image_name} ./{framework_name}"
        if subprocess.call(build_cmd, shell=True) != 0:
            print("ERREUR : Le build a échoué.")
            return
    else:
        print(f"\n 1/3 Image {image_name} déjà présente (Cache)")

    print(f" 2/3 Démarrage du pipeline...")
    
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
    print(f"\n--- FIN {framework_name.upper()} ---")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <nom_du_framework> [--rebuild]")
    else:
        fw = sys.argv[1]
        rebuild = "--rebuild" in sys.argv
        run_framework(fw, force_rebuild=rebuild)