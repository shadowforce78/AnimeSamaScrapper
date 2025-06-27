# Script PowerShell pour mettre à jour le service AnimeSamaScraper
# Exécuter en tant qu'administrateur

param(
    [switch]$Force,
    [switch]$SkipTests,
    [switch]$Backup
)

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "     MISE À JOUR DU SERVICE ANIMESAMASCRAPER" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier les privilèges administrateur
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERREUR: Ce script doit être exécuté en tant qu'administrateur." -ForegroundColor Red
    Write-Host "Relancez PowerShell en tant qu'administrateur et réessayez." -ForegroundColor Red
    exit 1
}

try {
    # Étape 1: Sauvegarde (optionnelle)
    if ($Backup) {
        Write-Host "[BACKUP] Création d'une sauvegarde..." -ForegroundColor Yellow
        $backupDir = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        
        if (Test-Path "logs") {
            Copy-Item "logs" "$backupDir/logs" -Recurse -Force
            Write-Host "Logs sauvegardés dans $backupDir/logs" -ForegroundColor Green
        }
        
        if (Test-Path "anime_data.json") {
            Copy-Item "anime_data.json" "$backupDir/" -Force
            Write-Host "Données sauvegardées dans $backupDir/" -ForegroundColor Green
        }
    }

    # Étape 2: Vérifier et arrêter le service
    Write-Host "[1/6] Vérification du statut du service..." -ForegroundColor Blue
    $service = Get-Service -Name "AnimeSamaScraper" -ErrorAction SilentlyContinue
    
    if ($service) {
        Write-Host "Service AnimeSamaScraper détecté (Status: $($service.Status))" -ForegroundColor Green
        
        if ($service.Status -eq "Running") {
            Write-Host "[2/6] Arrêt du service..." -ForegroundColor Blue
            Stop-Service -Name "AnimeSamaScraper" -Force
            Start-Sleep -Seconds 3
            Write-Host "Service arrêté avec succès." -ForegroundColor Green
        }
    } else {
        Write-Host "Aucun service AnimeSamaScraper détecté." -ForegroundColor Yellow
    }

    # Étape 3: Mise à jour Git
    Write-Host "[3/6] Mise à jour du code depuis Git..." -ForegroundColor Blue
    
    # Vérifier si on est dans un repo Git
    if (-not (Test-Path ".git")) {
        throw "Ce répertoire n'est pas un dépôt Git valide."
    }
    
    # Git fetch
    $gitFetch = Start-Process -FilePath "git" -ArgumentList "fetch" -Wait -PassThru -NoNewWindow
    if ($gitFetch.ExitCode -ne 0) {
        throw "Erreur lors de git fetch"
    }
    
    # Git pull
    $gitPull = Start-Process -FilePath "git" -ArgumentList "pull" -Wait -PassThru -NoNewWindow
    if ($gitPull.ExitCode -ne 0) {
        throw "Erreur lors de git pull"
    }
    
    Write-Host "Code mis à jour avec succès." -ForegroundColor Green

    # Étape 4: Vérifier les dépendances
    Write-Host "[4/6] Vérification des dépendances Python..." -ForegroundColor Blue
    
    $pythonTest = Start-Process -FilePath "python" -ArgumentList "-c", "import requests, bs4, pymongo, dotenv, schedule" -Wait -PassThru -NoNewWindow -RedirectStandardError NUL
    
    if ($pythonTest.ExitCode -ne 0) {
        Write-Host "Installation des dépendances manquantes..." -ForegroundColor Yellow
        $pipInstall = Start-Process -FilePath "pip" -ArgumentList "install", "-r", "requirements.txt" -Wait -PassThru -NoNewWindow
        if ($pipInstall.ExitCode -ne 0) {
            throw "Impossible d'installer les dépendances Python"
        }
        Write-Host "Dépendances installées avec succès." -ForegroundColor Green
    } else {
        Write-Host "Toutes les dépendances sont présentes." -ForegroundColor Green
    }

    # Étape 5: Tests (optionnel)
    if (-not $SkipTests) {
        Write-Host "[5/6] Exécution des tests..." -ForegroundColor Blue
        
        if (Test-Path "test_updated_scripts.py") {
            $testResult = Start-Process -FilePath "python" -ArgumentList "test_updated_scripts.py" -Wait -PassThru -NoNewWindow
            
            if ($testResult.ExitCode -ne 0) {
                Write-Host "ATTENTION: Les tests ont échoué." -ForegroundColor Red
                
                if (-not $Force) {
                    $continue = Read-Host "Voulez-vous continuer malgré les erreurs? (y/N)"
                    if ($continue -ne "y" -and $continue -ne "Y") {
                        throw "Mise à jour annulée par l'utilisateur"
                    }
                }
            } else {
                Write-Host "Tests réussis." -ForegroundColor Green
            }
        } else {
            Write-Host "Fichier de tests non trouvé, passage à l'étape suivante." -ForegroundColor Yellow
        }
    } else {
        Write-Host "[5/6] Tests ignorés (option -SkipTests activée)." -ForegroundColor Yellow
    }

    # Étape 6: Redémarrer le service
    Write-Host "[6/6] Redémarrage du service..." -ForegroundColor Blue
    
    if ($service) {
        Start-Service -Name "AnimeSamaScraper"
        Start-Sleep -Seconds 3
        
        $updatedService = Get-Service -Name "AnimeSamaScraper"
        if ($updatedService.Status -eq "Running") {
            Write-Host "Service redémarré avec succès." -ForegroundColor Green
        } else {
            Write-Host "ATTENTION: Le service ne semble pas fonctionner correctement." -ForegroundColor Red
        }
    } else {
        Write-Host "Aucun service à redémarrer. Installation manuelle requise." -ForegroundColor Yellow
        Write-Host "Exécutez: ./install_service.sh" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "        MISE À JOUR TERMINÉE AVEC SUCCÈS" -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""

    # Afficher le statut final
    Write-Host "Statut final du service:" -ForegroundColor Blue
    Get-Service -Name "AnimeSamaScraper" -ErrorAction SilentlyContinue | Format-Table Name, Status, StartType

    # Informations sur les logs
    $today = Get-Date -Format "yyyyMMdd"
    $logFile = "logs\anime_sama_scraper_$today.log"
    Write-Host "Pour consulter les logs d'aujourd'hui:" -ForegroundColor Blue
    Write-Host "Get-Content $logFile -Tail 20" -ForegroundColor Gray

} catch {
    Write-Host ""
    Write-Host "ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "La mise à jour a échoué. Vérifiez les erreurs ci-dessus." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Appuyez sur Entrée pour terminer..." -ForegroundColor Gray
Read-Host
