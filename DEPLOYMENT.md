# Guide de déploiement du scraper Anime-Sama sur serveur

Ce document décrit comment déployer le script de scraping automatique pour Anime-Sama sur un serveur Linux.

## Prérequis

- Un serveur Linux (Ubuntu, Debian, etc.)
- Python 3.8 ou supérieur
- MongoDB installé et configuré
- Git (pour cloner le dépôt)

## Installation

### 1. Cloner le dépôt

```bash
git clone https://votre-repo/AnimeSamaScrapper.git
cd AnimeSamaScrapper
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration de MongoDB

Créez un fichier `.env` à la racine du projet avec vos informations de connexion MongoDB:

```
MONGO_URL=mongodb://utilisateur:motdepasse@hote:port/database?options
```

Remplacez `utilisateur`, `motdepasse`, `hote`, `port` et `database` par vos propres valeurs.

### 5. Tester le script

Exécutez le script manuellement pour vérifier qu'il fonctionne correctement:

```bash
python daily_scraper.py --now
```

Cette commande va exécuter immédiatement le processus de scraping et mettre à jour la base de données.

### 6. Installer le service systemd

Le service systemd permettra au script de s'exécuter automatiquement au démarrage du serveur et de redémarrer en cas d'échec.

Utilisez le script d'installation fourni:

```bash
sudo ./install_service.sh
```

Suivez les instructions à l'écran pour configurer le service.

## Utilisation

### Vérifier l'état du service

```bash
sudo systemctl status anime-sama-scraper.service
```

### Démarrer/Arrêter/Redémarrer le service

```bash
sudo systemctl start anime-sama-scraper.service
sudo systemctl stop anime-sama-scraper.service
sudo systemctl restart anime-sama-scraper.service
```

### Consulter les logs

```bash
# Voir les logs du service
sudo journalctl -u anime-sama-scraper.service

# Suivre les logs en temps réel
sudo journalctl -u anime-sama-scraper.service -f
```

Vous pouvez également consulter les logs dans le dossier `logs/` du projet.

## Configuration avancée

### Modifier l'heure d'exécution

Par défaut, le script s'exécute tous les jours à minuit (00:00). Pour modifier cette heure:

1. Ouvrez le fichier `daily_scraper.py`
2. Recherchez la ligne `schedule.every().day.at("00:00").do(run_scheduled_job)`
3. Changez "00:00" par l'heure souhaitée au format 24h

Puis redémarrez le service:

```bash
sudo systemctl restart anime-sama-scraper.service
```

### Gérer les ressources

Si le script consomme trop de ressources, vous pouvez le limiter avec systemd en ajoutant ces lignes dans le fichier de service:

```
[Service]
CPUQuota=50%
MemoryLimit=1G
```

Puis rechargez systemd:

```bash
sudo systemctl daemon-reload
sudo systemctl restart anime-sama-scraper.service
```

## Dépannage

### Le service ne démarre pas

Vérifiez les journaux:

```bash
sudo journalctl -u anime-sama-scraper.service -n 50
```

### Problèmes de connexion à MongoDB

Vérifiez:
1. Le fichier `.env` avec les bonnes informations de connexion
2. Que MongoDB est en cours d'exécution
3. Que les règles de pare-feu permettent la connexion

### Problèmes de mémoire

Si le script consomme trop de mémoire, ajustez la limite dans le fichier de service et envisagez d'optimiser le code pour traiter les données par lots.
