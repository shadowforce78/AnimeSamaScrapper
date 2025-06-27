# Script de surveillance du service AnimeSamaScraper
# À exécuter régulièrement pour vérifier l'état du service

param(
    [switch]$Detailed,
    [switch]$RestartIfDown,
    [int]$EmailAlert = 0
)

$serviceName = "AnimeSamaScraper"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Write-Host "=== SURVEILLANCE ANIMESAMASCRAPER - $timestamp ===" -ForegroundColor Cyan

# 1. Vérifier le statut du service
Write-Host "`n[CHECK 1] Statut du service Windows:" -ForegroundColor Blue
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if (-not $service) {
    Write-Host "❌ Service '$serviceName' non trouvé" -ForegroundColor Red
    $serviceOk = $false
} elseif ($service.Status -ne "Running") {
    Write-Host "⚠️  Service '$serviceName' ne fonctionne pas (Status: $($service.Status))" -ForegroundColor Yellow
    $serviceOk = $false
    
    if ($RestartIfDown) {
        Write-Host "🔄 Tentative de redémarrage..." -ForegroundColor Blue
        try {
            Start-Service -Name $serviceName
            Start-Sleep -Seconds 5
            $service = Get-Service -Name $serviceName
            if ($service.Status -eq "Running") {
                Write-Host "✅ Service redémarré avec succès" -ForegroundColor Green
                $serviceOk = $true
            } else {
                Write-Host "❌ Échec du redémarrage" -ForegroundColor Red
                $serviceOk = $false
            }
        } catch {
            Write-Host "❌ Erreur lors du redémarrage: $($_.Exception.Message)" -ForegroundColor Red
            $serviceOk = $false
        }
    }
} else {
    Write-Host "✅ Service '$serviceName' fonctionne correctement" -ForegroundColor Green
    $serviceOk = $true
}

# 2. Vérifier les logs récents
Write-Host "`n[CHECK 2] Analyse des logs récents:" -ForegroundColor Blue
$today = Get-Date -Format "yyyyMMdd"
$logFile = "logs\anime_sama_scraper_$today.log"

if (Test-Path $logFile) {
    $logContent = Get-Content $logFile -ErrorAction SilentlyContinue
    
    if ($logContent) {
        # Chercher les dernières exécutions
        $lastExecutions = $logContent | Select-String "DÉBUT DU PROCESSUS" | Select-Object -Last 3
        $errors = $logContent | Select-String "ERROR" | Select-Object -Last 5
        $warnings = $logContent | Select-String "WARNING" | Select-Object -Last 5
        
        Write-Host "📊 Dernières exécutions ($($lastExecutions.Count)):" -ForegroundColor White
        foreach ($exec in $lastExecutions) {
            Write-Host "   $exec" -ForegroundColor Gray
        }
        
        if ($errors.Count -gt 0) {
            Write-Host "⚠️  Erreurs récentes ($($errors.Count)):" -ForegroundColor Red
            foreach ($error in $errors) {
                Write-Host "   $error" -ForegroundColor Red
            }
            $hasErrors = $true
        } else {
            Write-Host "✅ Aucune erreur récente" -ForegroundColor Green
            $hasErrors = $false
        }
        
        if ($warnings.Count -gt 0 -and $Detailed) {
            Write-Host "⚠️  Avertissements récents ($($warnings.Count)):" -ForegroundColor Yellow
            foreach ($warning in $warnings) {
                Write-Host "   $warning" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "⚠️  Fichier de log vide" -ForegroundColor Yellow
        $hasErrors = $false
    }
} else {
    Write-Host "⚠️  Fichier de log d'aujourd'hui non trouvé: $logFile" -ForegroundColor Yellow
    $hasErrors = $false
}

# 3. Vérifier l'espace disque
Write-Host "`n[CHECK 3] Espace disque:" -ForegroundColor Blue
$drive = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DeviceID -eq (Get-Location).Drive.Name + ":" }
if ($drive) {
    $freeSpaceGB = [math]::Round($drive.FreeSpace / 1GB, 2)
    $totalSpaceGB = [math]::Round($drive.Size / 1GB, 2)
    $percentFree = [math]::Round(($drive.FreeSpace / $drive.Size) * 100, 1)
    
    Write-Host "💾 Espace libre: $freeSpaceGB GB / $totalSpaceGB GB ($percentFree%)" -ForegroundColor White
    
    if ($percentFree -lt 10) {
        Write-Host "⚠️  ATTENTION: Espace disque faible!" -ForegroundColor Red
        $diskOk = $false
    } elseif ($percentFree -lt 20) {
        Write-Host "⚠️  Espace disque en diminution" -ForegroundColor Yellow
        $diskOk = $true
    } else {
        Write-Host "✅ Espace disque suffisant" -ForegroundColor Green
        $diskOk = $true
    }
} else {
    Write-Host "⚠️  Impossible de vérifier l'espace disque" -ForegroundColor Yellow
    $diskOk = $true
}

# 4. Vérifier la connectivité réseau (test simple)
Write-Host "`n[CHECK 4] Connectivité réseau:" -ForegroundColor Blue
try {
    $testConnection = Test-Connection -ComputerName "anime-sama.fr" -Count 1 -Quiet -ErrorAction SilentlyContinue
    if ($testConnection) {
        Write-Host "✅ Connexion vers anime-sama.fr OK" -ForegroundColor Green
        $networkOk = $true
    } else {
        Write-Host "❌ Impossible de joindre anime-sama.fr" -ForegroundColor Red
        $networkOk = $false
    }
} catch {
    Write-Host "⚠️  Test de connexion échoué: $($_.Exception.Message)" -ForegroundColor Yellow
    $networkOk = $false
}

# 5. Résumé global
Write-Host "`n[RÉSUMÉ] État global du système:" -ForegroundColor Cyan
$overallStatus = $serviceOk -and (-not $hasErrors) -and $diskOk -and $networkOk

if ($overallStatus) {
    Write-Host "🎉 TOUT VA BIEN - Système opérationnel" -ForegroundColor Green
    $exitCode = 0
} else {
    Write-Host "⚠️  PROBLÈMES DÉTECTÉS - Attention requise" -ForegroundColor Red
    Write-Host "   - Service OK: $serviceOk" -ForegroundColor $(if($serviceOk){"Green"}else{"Red"})
    Write-Host "   - Pas d'erreurs: $(-not $hasErrors)" -ForegroundColor $(if(-not $hasErrors){"Green"}else{"Red"})
    Write-Host "   - Disque OK: $diskOk" -ForegroundColor $(if($diskOk){"Green"}else{"Red"})
    Write-Host "   - Réseau OK: $networkOk" -ForegroundColor $(if($networkOk){"Green"}else{"Red"})
    $exitCode = 1
}

# 6. Actions recommandées si problème
if (-not $overallStatus) {
    Write-Host "`n[ACTIONS RECOMMANDÉES]:" -ForegroundColor Yellow
    
    if (-not $serviceOk) {
        Write-Host "• Redémarrer le service: net start $serviceName" -ForegroundColor White
        Write-Host "• Vérifier les logs pour plus de détails" -ForegroundColor White
    }
    
    if ($hasErrors) {
        Write-Host "• Analyser les erreurs dans les logs" -ForegroundColor White
        Write-Host "• Vérifier la configuration de la base de données" -ForegroundColor White
    }
    
    if (-not $diskOk) {
        Write-Host "• Nettoyer l'espace disque" -ForegroundColor White
        Write-Host "• Archiver les anciens logs" -ForegroundColor White
    }
    
    if (-not $networkOk) {
        Write-Host "• Vérifier la connexion Internet" -ForegroundColor White
        Write-Host "• Vérifier si anime-sama.fr est accessible" -ForegroundColor White
    }
}

Write-Host "`n=== FIN DE LA SURVEILLANCE ===" -ForegroundColor Cyan

# Option: envoyer une alerte email (à implémenter selon vos besoins)
if ($EmailAlert -and -not $overallStatus) {
    Write-Host "`n📧 Alerte email activée - implémentation nécessaire" -ForegroundColor Blue
    # Ici vous pourriez ajouter l'envoi d'email avec Send-MailMessage
}

exit $exitCode
