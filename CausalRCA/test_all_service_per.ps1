$output = "cpu_all_service_gamma5.txt"

# Fonction pour écrire une ligne dans la console et dans le fichier
function Write-Log {
    param([string]$message)
    $message
    Add-Content -Path $output -Value $message
}

# Écrire la date de début
Write-Log (Get-Date -Format "yyyy-MM-dd HH:mm:ss")

for ($i = 0; $i -le 6; $i++) {
    Write-Log $i
    for ($j = 1; $j -le 10; $j++) {
        Write-Log $j
        # Exécuter la commande Python et capturer la sortie
        $pythonOutput = python train_all_services.py --indx=$i --atype='cpu-hog1_' --gamma=0.5 2>&1
        # Afficher et écrire la sortie dans le fichier
        Write-Log $pythonOutput
    }
    Write-Log "-----one service finish-----"
}

# Écrire la date de fin
Write-Log (Get-Date -Format "yyyy-MM-dd HH:mm:ss")