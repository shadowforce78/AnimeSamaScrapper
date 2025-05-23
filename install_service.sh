#!/bin/bash
# Script d'installation du service de scraping Anime-Sama

# Vérifier si l'utilisateur est root
if [[ $EUID -ne 0 ]]; then
   echo "Ce script doit être exécuté en tant que root" 
   exit 1
fi

# Définir le chemin d'installation
read -p "Entrez le chemin complet vers le dossier AnimeSamaScrapper: " INSTALL_PATH
if [ ! -d "$INSTALL_PATH" ]; then
    echo "Le dossier n'existe pas!"
    exit 1
fi

# Définir l'utilisateur qui exécutera le service
read -p "Entrez le nom d'utilisateur qui exécutera le service: " SERVICE_USER
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "L'utilisateur $SERVICE_USER n'existe pas!"
    exit 1
fi

# Mise à jour du fichier de service
sed -i "s|User=youruser|User=$SERVICE_USER|g" "$INSTALL_PATH/anime-sama-scraper.service"
sed -i "s|WorkingDirectory=/path/to/AnimeSamaScrapper|WorkingDirectory=$INSTALL_PATH|g" "$INSTALL_PATH/anime-sama-scraper.service"
sed -i "s|ExecStart=/usr/bin/python3 /path/to/AnimeSamaScrapper/daily_scraper.py|ExecStart=/usr/bin/python3 $INSTALL_PATH/daily_scraper.py|g" "$INSTALL_PATH/anime-sama-scraper.service"

# Copier le fichier de service
cp "$INSTALL_PATH/anime-sama-scraper.service" /etc/systemd/system/

# Recharger systemd
systemctl daemon-reload

# Activer le service
systemctl enable anime-sama-scraper.service

# Démarrer le service
systemctl start anime-sama-scraper.service

# Vérifier l'état du service
systemctl status anime-sama-scraper.service

echo "Installation terminée. Le service est configuré pour démarrer automatiquement au boot."
echo "Vous pouvez vérifier les logs avec: journalctl -u anime-sama-scraper.service -f"
