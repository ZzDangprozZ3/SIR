# Définition du fichier de sortie
$output = "cpu_latency_gamma5.txt"

# Fonction pour écrire la date/heure dans le fichier et afficher à l'écran
function Write-DateTime {
    $date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $date | Tee-Object -FilePath $output -Append
}

# Écrire la date/heure de début
Write-DateTime

# Boucle externe de 0 à 6 inclus
for ($i = 0; $i -le 6; $i++) {
    # Écrire la valeur de i
    $i | Tee-Object -FilePath $output -Append

    # Boucle interne de 1 à 10 inclus
    for ($j = 1; $j -le 10; $j++) {
        # Écrire la valeur de j
        $j | Tee-Object -FilePath $output -Append

        # Exécuter le script Python avec les arguments, rediriger la sortie vers le fichier et l'écran
        # Note : Assurez-vous que python est dans le PATH
        python train_latency.py --indx=$i --atype='cpu-hog1_' --gamma=0.5 | Tee-Object -FilePath $output -Append
    }

    # Marque la fin d'un service
    "-----one service finish-----" | Tee-Object -FilePath $output -Append
}

# Écrire la date/heure de fin
Write-DateTime