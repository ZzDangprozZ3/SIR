import subprocess
import sys

def run_command(command, description):
    print(f"--- En cours: {description} ---")
    try:
        # shell=True giúp chạy các lệnh giống như khi gõ vào CMD/PowerShell
        result = subprocess.run(command, shell=True, check=True, text=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error at '{description}': {e}")
        sys.exit(1) # Dừng toàn bộ nếu một bước bị lỗi

def main():
    # Bước 1: Chạy file a.py
    run_command("python traitementdata.py", "Execution traitementdata.py")

    # Bước 2: Chạy Docker Compose
    # Lệnh này sẽ chạy container và đợi nó kết thúc (run)
    run_command("docker compose run --rm --build traceanomaly", "Execution Docker Compose")

    # Bước 3: Chạy file detection_anomaly.py
    run_command("python detection_anomaly.py", "Execution file detectionanomaly.py")

    print("--- FINISHED! ---")

if __name__ == "__main__":
    main()