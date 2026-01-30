import os
import sys
import subprocess

DATA_DIR_NAME = "NetMob23"
ENTRYPOINT_SCRIPT = "pipeline.sh"

def check_data_presence(data_path):
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
    
    if fw_lower == "alertrca":
        print(f"\n>>> Lancement de AlertRCA via Docker-Compose...")
        subprocess.call("docker-compose run --rm --build app", shell=True, cwd=framework_dir)
        print(f"\nFIN {framework_name.upper()}")
        return
    
    if fw_lower == "traceanomaly":
        print(f"\n>>> Lancement de TraceAnomaly via script Python...")
        subprocess.call(f"{sys.executable} main.py", shell=True, cwd=framework_dir)
        print(f"\nFIN {framework_name.upper()}")
        return
    
    if fw_lower == "aoc_ids":
        print(f"\n>>> Lancement de AOC_IDS via Pipeline Automatisé...")
        print("=" * 80)
        print("FRAMEWORK: AOC-IDS (Anomaly-based Online Continual Intrusion Detection)")
        print("PIPELINE : Conversion + Entraînement + Validation")
        print("DURÉE ESTIMÉE : 2-4 heures")
        print("=" * 80)
        
        pipeline_script = os.path.join(framework_dir, "run_complete_pipeline.sh")
        if not os.path.exists(pipeline_script):
            print(f"\nERREUR: Le script 'run_complete_pipeline.sh' n'existe pas dans {framework_dir}")
            return
        
        aoc_data_dir = os.path.join(framework_dir, "Dataset NetMob23")
        
        if not os.path.exists(aoc_data_dir):
            print(f"\n[INFO] Création d'un lien symbolique vers {DATA_DIR_NAME}...")
            try:
                os.symlink(data_dir, aoc_data_dir)
                print(f"[OK] Lien créé: {aoc_data_dir} -> {data_dir}")
            except Exception as e:
                print(f"[ERREUR] Impossible de créer le lien symbolique: {e}")
                print(f"[INFO] Tentative de copie du dataset...")
                subprocess.call(f'cp -r "{data_dir}" "{aoc_data_dir}"', shell=True)
        
        subprocess.call(f"chmod +x {pipeline_script}", shell=True)
        
        print(f"\n[INFO] Lancement du pipeline AOC_IDS...")
        result = subprocess.call(f"bash run_complete_pipeline.sh", shell=True, cwd=framework_dir)
        
        if result == 0:
            print(f"\n{'=' * 80}")
            print(f"FIN {framework_name.upper()} - Pipeline terminé avec succès")
            print(f"{'=' * 80}")
            print(f"\nRÉSULTATS DISPONIBLES DANS:")
            print(f"   - {os.path.join(framework_dir, 'output', 'Facebook', 'validation_report.txt')}")
            print(f"   - {os.path.join(framework_dir, 'output', 'Netflix', 'validation_report.txt')}")
        else:
            print(f"\nERREUR lors de l'exécution du pipeline AOC_IDS")
        
        return
    
    if fw_lower == "anoshift":
        print(f"\n>>> Lancement de AnoShift...")
        print("=" * 80)
        print("FRAMEWORK: AnoShift (Distribution Shift Benchmark for Anomaly Detection)")
        print("PIPELINE : Conversion Parquet + Détection COPOD")
        print("DURÉE ESTIMÉE : 20-30 minutes")
        print("=" * 80)
        
        parquet_dir = os.path.join(framework_dir, "datasets", "NetMob23_Parquet")
        convert_script = os.path.join(framework_dir, "convert_netmob_to_parquet.py")
        
        if not os.path.exists(parquet_dir) or not os.listdir(parquet_dir):
            print(f"\n[1/4] Conversion des données TXT vers Parquet...")
            if os.path.exists(convert_script):
                subprocess.call(
                    f"{sys.executable} {convert_script} --input {data_dir}",
                    shell=True,
                    cwd=framework_dir
                )
            else:
                print(f"ERREUR : Script de conversion introuvable : {convert_script}")
                return
        else:
            print(f"\n[1/4] Données Parquet déjà présentes (Cache)")
        
        image_name = "anoshift_img"
        should_build = force_rebuild or not image_exists(image_name)
        
        if should_build:
            print(f"[2/4] Construction de l'image Docker ({image_name})...")
            build_cmd = f"docker build -t {image_name} ./{framework_name}"
            if subprocess.call(build_cmd, shell=True) != 0:
                print("ERREUR : Le build Docker a échoué.")
                return
        else:
            print(f"[2/4] Image {image_name} déjà présente (Cache)")
        
        print(f"[3/4] Détection d'anomalies avec COPOD...")
        
        framework_dir_clean = framework_dir.replace('\\', '/')
        parquet_dir_clean = parquet_dir.replace('\\', '/')
        
        for app in ["facebook", "netflix"]:
            print(f"\n     >>> Traitement de {app.upper()}...")
            docker_cmd = (
                f"docker run --rm "
                f"-v \"{parquet_dir_clean}:/app/datasets/NetMob23_Parquet\" "
                f"-v \"{framework_dir_clean}/baselines_OOD_setup:/app/baselines_OOD_setup\" "
                f"{image_name} "
                f"python baselines_OOD_setup/run_pyod_netmob.py copod {app} full"
            )
            subprocess.call(docker_cmd, shell=True)
        
        print(f"\n[4/4] Résultats générés")
        print(f"\n{'=' * 80}")
        print(f"FIN {framework_name.upper()} - Pipeline terminé avec succès")
        print(f"{'=' * 80}")
        print(f"\nRÉSULTATS DISPONIBLES DANS:")
        print(f"   - {os.path.join(framework_dir, 'baselines_OOD_setup', 'results_facebook_full.txt')}")
        print(f"   - {os.path.join(framework_dir, 'baselines_OOD_setup', 'results_netflix_full.txt')}")
        return

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
    print(f"\n FIN {framework_name.upper()} ")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <nom_du_framework> [--rebuild]")
    else:
        fw = sys.argv[1]
        rebuild = "--rebuild" in sys.argv
        run_framework(fw, force_rebuild=rebuild)
