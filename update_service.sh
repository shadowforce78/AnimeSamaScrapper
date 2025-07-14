#!/bin/bash

# Script de mise à jour du service AnimeSamaScraper
# Usage: ./update_service.sh
# Doit être exécuté avec les droits sudo pour gérer le service systemd

set -e  # Arrêter le script en cas d'erreur

SERVICE_NAME="anime-sama-scraper"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==============================================="
echo "     MISE A JOUR DU SERVICE ANIMESAMASCRAPER"
echo "==============================================="
echo

# Vérifier si le script est exécuté avec sudo
if [[ $EUID -eq 0 ]]; then
    echo "ERREUR: Ce script ne doit PAS être exécuté avec sudo."
    echo "Il utilisera sudo automatiquement quand nécessaire."
    exit 1
fi

# Vérifier si systemctl est disponible
if ! command -v systemctl &> /dev/null; then
    echo "ERREUR: systemctl n'est pas disponible. Ce script nécessite systemd."
    exit 1
fi

echo "[1/7] Vérification du statut actuel du service..."
if sudo systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "Service $SERVICE_NAME détecté et actif."
    
    echo "[2/7] Arrêt du service..."
    if sudo systemctl stop "$SERVICE_NAME"; then
        echo "Service arrêté avec succès."
    else
        echo "ATTENTION: Impossible d'arrêter le service. Continuation..."
    fi
elif sudo systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "Service $SERVICE_NAME détecté mais inactif."
else
    echo "Aucun service $SERVICE_NAME détecté."
fi

echo "[3/7] Mise à jour du code depuis Git..."
cd "$SCRIPT_DIR"

if ! git fetch; then
    echo "ERREUR: Impossible d'exécuter git fetch."
    echo "Vérifiez que Git est installé et que vous êtes dans un dépôt Git."
    exit 1
fi

if ! git pull; then
    echo "ERREUR: Impossible d'exécuter git pull."
    echo "Vérifiez qu'il n'y a pas de conflits à résoudre."
    exit 1
fi

echo "Code mis à jour avec succès."

echo "[4/7] Vérification de l'environnement Python..."
# Vérifier si Python 3 est disponible
if ! command -v python3 &> /dev/null; then
    echo "ERREUR: Python 3 n'est pas installé."
    exit 1
fi

# Vérifier si pip est disponible
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "ERREUR: pip n'est pas disponible."
    exit 1
fi

echo "[5/7] Vérification et installation des dépendances Python..."
if ! python3 -c "import requests, bs4, pymongo, dotenv, schedule" &> /dev/null; then
    echo "Installation des dépendances manquantes..."
    if command -v pip3 &> /dev/null; then
        pip3 install -r requirements.txt --user
    else
        python3 -m pip install -r requirements.txt --user
    fi
    
    if [[ $? -ne 0 ]]; then
        echo "ERREUR: Impossible d'installer les dépendances."
        exit 1
    fi
else
    echo "Toutes les dépendances sont déjà installées."
fi

echo "[6/7] Test du script principal et de la nouvelle fonctionnalité planning..."

# Test basique des imports principaux
if ! python3 -c "
try:
    from add_to_db import insert_mangas_to_db, insert_planning_to_db
    from planning import scrape_planning
    print('✅ Tous les imports fonctionnent correctement')
except ImportError as e:
    print(f'❌ Erreur d\'import: {e}')
    exit(1)
"; then
    echo "ERREUR: Les imports principaux ont échoué."
    exit 1
fi

# Test du fichier de test s'il existe
if [[ -f "test_updated_scripts.py" ]]; then
    if ! python3 test_updated_scripts.py; then
        echo "ATTENTION: Les tests ont échoué. Le service peut ne pas fonctionner correctement."
        read -p "Voulez-vous continuer malgré les erreurs ? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Mise à jour annulée."
            exit 1
        fi
    fi
else
    echo "Fichier de test non trouvé, test d'import réussi."
fi

echo "[7/7] Redémarrage du service..."
if sudo systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    if sudo systemctl start "$SERVICE_NAME"; then
        echo "Service redémarré avec succès."
    else
        echo "ERREUR: Impossible de redémarrer le service."
        echo "Vous devrez le redémarrer manuellement avec: sudo systemctl start $SERVICE_NAME"
        exit 1
    fi
else
    echo "Aucun service à redémarrer. Installation manuelle requise."
    echo "Exécutez: sudo ./install_service.sh"
fi

echo
echo "==============================================="
echo "        MISE A JOUR TERMINEE AVEC SUCCES"
echo "==============================================="
echo

# Afficher le statut final du service
echo "Statut final du service:"
sudo systemctl status "$SERVICE_NAME" --no-pager -l

echo
echo "Pour consulter les logs en temps réel:"
echo "sudo journalctl -u $SERVICE_NAME -f"
echo
echo "Pour consulter les logs d'application:"
current_date=$(date +%Y%m%d)
echo "tail -f logs/anime_sama_scraper_${current_date}.log"

echo
echo "Appuyez sur Entrée pour terminer..."
read
