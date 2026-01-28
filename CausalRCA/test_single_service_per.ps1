$output = "memory_single_service_eta1000.txt"

function Write-Log {
    param([string]$message)
    $message
    Add-Content -Path $output -Value $message
}

# Écrire la date de début
Write-Log (Get-Date -Format "yyyy-MM-dd HH:mm:ss")

for ($i = 6; $i -le 6; $i++) {
    Write-Log $i
    for ($j = 1; $j -le 10; $j++) {
        Write-Log $j
        $pythonOutput = python train_single_service.py --indx=$i --atype='memory-leak1_' --eta=1000 2>&1
        Write-Log $pythonOutput
    }
    Write-Log "-----one service finish-----"
}

# Écrire la date de fin
Write-Log (Get-Date -Format "yyyy-MM-dd HH:mm:ss")