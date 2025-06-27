@echo off
setlocal enabledelayedexpansion

echo ===============================================
echo     MISE A JOUR DU SERVICE ANIMESAMASCRAPER
echo ===============================================
echo.

:: Vérifier si le script est exécuté en tant qu'administrateur
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERREUR: Ce script doit etre execute en tant qu'administrateur.
    echo Clic droit sur le fichier et "Executer en tant qu'administrateur"
    pause
    exit /b 1
)

echo [1/6] Verification du statut actuel du service...
sc query AnimeSamaScraper >nul 2>&1
if %errorLevel% equ 0 (
    echo Service AnimeSamaScraper detecte.
    
    echo [2/6] Arret du service...
    net stop AnimeSamaScraper
    if %errorLevel% neq 0 (
        echo ATTENTION: Impossible d'arreter le service. Continuation...
    ) else (
        echo Service arrete avec succes.
    )
) else (
    echo Aucun service AnimeSamaScraper detecte.
)

echo [3/6] Mise a jour du code depuis Git...
git fetch
if %errorLevel% neq 0 (
    echo ERREUR: Impossible d'executer git fetch.
    echo Verifiez que Git est installe et que vous etes dans un depot Git.
    pause
    exit /b 1
)

git pull
if %errorLevel% neq 0 (
    echo ERREUR: Impossible d'executer git pull.
    echo Verifiez qu'il n'y a pas de conflits a resoudre.
    pause
    exit /b 1
)

echo Code mis a jour avec succes.

echo [4/6] Verification des dependances Python...
python -c "import requests, bs4, pymongo, dotenv, schedule" >nul 2>&1
if %errorLevel% neq 0 (
    echo Installation des dependances manquantes...
    pip install -r requirements.txt
    if %errorLevel% neq 0 (
        echo ERREUR: Impossible d'installer les dependances.
        pause
        exit /b 1
    )
)

echo [5/6] Test du script principal...
python test_updated_scripts.py
if %errorLevel% neq 0 (
    echo ATTENTION: Les tests ont echoue. Le service peut ne pas fonctionner correctement.
    choice /C YN /M "Voulez-vous continuer malgre les erreurs"
    if !errorlevel! equ 2 (
        echo Mise a jour annulee.
        pause
        exit /b 1
    )
)

echo [6/6] Redemarrage du service...
sc query AnimeSamaScraper >nul 2>&1
if %errorLevel% equ 0 (
    net start AnimeSamaScraper
    if %errorLevel% neq 0 (
        echo ERREUR: Impossible de redemarrer le service.
        echo Vous devrez le redemarrer manuellement avec: net start AnimeSamaScraper
        pause
        exit /b 1
    ) else (
        echo Service redémarre avec succes.
    )
) else (
    echo Aucun service a redemarrer. Installation manuelle requise.
    echo Executez: install_service.sh
)

echo.
echo ===============================================
echo        MISE A JOUR TERMINEE AVEC SUCCES
echo ===============================================
echo.

:: Afficher le statut final du service
echo Statut final du service:
sc query AnimeSamaScraper

echo.
echo Pour consulter les logs:
for /f "tokens=2 delims==" %%i in ('wmic OS Get localdatetime /value') do set datetime=%%i
set "date_formatted=!datetime:~0,4!!datetime:~4,2!!datetime:~6,2!"
echo type logs\anime_sama_scraper_!date_formatted!.log

echo.
echo Appuyez sur une touche pour terminer...
pause >nul
