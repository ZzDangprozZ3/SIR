import os
import sys
import subprocess

# Configuration globale
DATA_DIR_NAME = "NetMob23"
ENTRYPOINT_SCRIPT = "pipeline.sh"

def run_framework(framework_name):

    root_dir = os.getcwd()
    framework_dir = os.path.join(root_dir, framework_name)
    data_dir = os.path.join(root_dir, DATA_DIR_NAME)

    if not os.path.isdir(framework_dir):
        print(f"ERREUR: Le dossier du framework '{framework_name}' n'existe pas.")
        return

    print(f"\n LANCEMENT DU FRAMEWORK : {framework_name.upper()}")

    # Construction de l'image Docker
    image_name = f"{framework_name.lower()}_img"
    print(f" Construction de l'image Docker ({image_name})...")
    
    build_cmd = f"docker build -t {image_name} ./{framework_name}"
    ret = subprocess.call(build_cmd, shell=True)
    if ret != 0:
        print("ERREUR: Échec de la construction Docker.")
        return

    
    print(f" Démarrage du conteneur...")
    
    
    docker_cmd = (
        f"docker run --rm "
        f"-v \"{data_dir}:/data\" "
        f"-v \"{framework_dir}:/app\" "
        f"{image_name} "
        f"bash {ENTRYPOINT_SCRIPT}"
    )
    
    print(f"Exécution du pipeline interne...")
    subprocess.call(docker_cmd, shell=True)
    
    print(f"\nFIN DU PROCESSUS {framework_name.upper()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <nom_du_framework>")
        print("Exemple: python main.py AWSCTD")
    else:
        run_framework(sys.argv[1])