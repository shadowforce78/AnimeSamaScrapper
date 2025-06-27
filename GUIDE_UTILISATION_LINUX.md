# 📚 Guide d'utilisation - AnimeSamaScraper (Linux)

## 🎯 Résumé des améliorations

Les scripts ont été optimisés pour un déploiement et une maintenance 100% Linux avec :
- 📖 Comptage précis des pages pour chaque chapitre
- 📊 Statistiques complètes (mangas, chapitres, pages)
- 🔄 Automatisation complète du processus avec systemd
- 💾 Stockage structuré en base de données MongoDB
- 📈 Suivi des métriques de contenu
- 🛠️ **Scripts de maintenance Linux automatisés**
- 🔍 **Surveillance continue du service**
- 📧 **Alertes et notifications (extensible)**

### 🚀 Workflow complet de mise à jour (Linux)
1. **Développement local** → Test avec `python test_updated_scripts.py`
2. **Commit et push** → `git add . && git commit -m "..." && git push`
3. **Mise à jour production** → `./update_service.sh`
4. **Surveillance** → `./monitor_service.sh --detailed`

## 📁 Scripts disponibles

### 1. `main.py` (Script principal)
- ✅ **Fonctionnalité principale** : Scraping complet des mangas avec comptage des pages
- ✅ **Nouvelle fonction** : `process_all_steps_in_order()` - Exécute les 4 étapes automatiquement
- ✅ **Amélioration** : Parse correctement les fichiers `episodes.js` au format JavaScript

### 2. `add_to_db.py` (Ajout en base de données)
- ✅ **Fonctionnalité principale** : Insertion des données scrapées dans MongoDB
- ✅ **Nouvelles données** : Stockage du `page_count`, `scan_id`, `episodes_url` pour chaque chapitre
- ✅ **Nouvelles statistiques** : Comptage total des pages, moyenne de pages par chapitre
- ✅ **Amélioration** : Affichage enrichi des recherches avec nombre de chapitres et pages

### 3. `daily_scraper.py` (Scraping automatique)
- ✅ **Fonctionnalité principale** : Scraping quotidien automatisé avec scheduler
- ✅ **Amélioration** : Utilise maintenant le processus complet (4 étapes) incluant le scraping des chapitres
- ✅ **Nouvelles options** : `--test-db` pour tester la connexion MongoDB
- ✅ **Logging amélioré** : Statistiques détaillées des chapitres et pages scrapés

### 4. `update_service.sh` (Mise à jour automatique)
- ✅ **Script de maintenance Linux** : Automatise la mise à jour du service
- ✅ **Fonctionnalités** : Arrêt/démarrage service, git pull, tests, vérifications
- ✅ **Sécurisé** : Vérifications à chaque étape, rollback possible

### 5. `monitor_service.sh` (Surveillance)
- ✅ **Surveillance complète** : Service, logs, espace disque, réseau
- ✅ **Options avancées** : Redémarrage automatique, alertes, rapports détaillés
- ✅ **Compatible cron** : Peut être automatisé pour surveillance continue

## 🚀 Utilisation

### Scraping manuel complet
```bash
# Exécuter le script principal (mode interactif)
python main.py

# Puis suivre les étapes 1→2→3→4 dans le menu
```

### Scraping automatique en arrière-plan
```bash
# Exécuter le scraping quotidien immédiatement
python daily_scraper.py --now

# Tester la connexion à la base de données
python daily_scraper.py --test-db
```

### Ajout manuel en base
```bash
# Ajouter les données du fichier JSON dans MongoDB
python add_to_db.py

# Le script utilise automatiquement anime_data.json
```

## 🗄️ Structure des données

### Collection `anime_list`
- Métadonnées des mangas
- **Nouveau** : `total_pages` - Total de pages pour tous les chapitres
- **Nouveau** : `scan_chapters` - Données complètes des scans

### Collection `chapters`
- Chapitres individuels
- **Nouveau** : `page_count` - Nombre de pages du chapitre
- **Nouveau** : `scan_id` - ID du scan source
- **Nouveau** : `episodes_url` - URL du fichier episodes.js

## 📈 Statistiques disponibles

Le script `add_to_db.py` affiche maintenant :
- Nombre total de mangas et chapitres
- **Nouveau** : Nombre total de pages indexées
- **Nouveau** : Moyenne de pages par chapitre
- Top 5 des mangas avec le plus de chapitres (avec nombre de pages)

## 🔧 Dépendances requises

```bash
# Installation des dépendances
pip install -r requirements.txt

# Ou manuellement :
pip install pymongo python-dotenv schedule requests beautifulsoup4
```

## 📝 Configuration MongoDB

Créer un fichier `.env` avec :
```env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/database_name
```

## ⚡ Tests

Pour vérifier que tout fonctionne :
```bash
python test_updated_scripts.py
```

## 🕐 Planification automatique

### Linux (Service systemd)
```bash
# Installer le service
sudo cp anime-sama-scraper.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable anime-sama-scraper
sudo systemctl start anime-sama-scraper

# Vérifier le statut
sudo systemctl status anime-sama-scraper
```

## 🔄 Mise à jour du service après modifications

Le script `update_service.sh` automatise complètement la mise à jour :

```bash
# Mise à jour automatique (recommandée)
./update_service.sh

# Le script effectue automatiquement :
# 1. Arrêt du service systemd
# 2. Mise à jour du code (git pull)
# 3. Installation des dépendances
# 4. Tests de validation
# 5. Redémarrage du service
```

### Vérification après mise à jour
```bash
# Vérifier le statut du service
sudo systemctl status anime-sama-scraper

# Consulter les logs pour vérifier le bon fonctionnement
tail -f logs/anime_sama_scraper_$(date +%Y%m%d).log

# Vérifier les logs systemd
journalctl -u anime-sama-scraper -f
```

### 📋 Bonnes pratiques pour les mises à jour

1. **Sauvegarde avant mise à jour** :
   ```bash
   # Sauvegarder la base de données
   mongodump --uri="your_mongo_url" --out=backup_before_update
   
   # Sauvegarder les logs
   cp -r logs logs_backup_$(date +%Y%m%d)
   ```

2. **Test en local avant déploiement** :
   ```bash
   # Tester le script en mode manuel
   python daily_scraper.py --now
   
   # Vérifier les nouvelles fonctionnalités
   python test_updated_scripts.py
   ```

3. **Surveillance après mise à jour** :
   ```bash
   # Surveiller les logs en temps réel
   tail -f logs/anime_sama_scraper_*.log
   ```

## 🔍 Surveillance et maintenance du service

### Script de surveillance Linux
```bash
# Vérification standard
./monitor_service.sh

# Vérification détaillée avec tous les logs
./monitor_service.sh --detailed

# Surveillance avec redémarrage automatique si nécessaire
./monitor_service.sh --restart

# Surveillance complète avec alertes
./monitor_service.sh --detailed --restart --email
```

### Commandes de surveillance essentielles
```bash
# Vérifier le statut du service
sudo systemctl status anime-sama-scraper

# Surveiller les logs en temps réel
tail -f logs/anime_sama_scraper_$(date +%Y%m%d).log

# Vérifier les dernières exécutions
grep "DÉBUT DU PROCESSUS" logs/anime_sama_scraper_*.log | tail -5

# Voir les erreurs récentes
grep "ERROR" logs/anime_sama_scraper_*.log | tail -10

# Vérifier les logs systemd
journalctl -u anime-sama-scraper --since "1 hour ago"
```

### Vérifications de santé périodiques
```bash
# Vérifier l'espace disque
df -h

# Vérifier l'usage mémoire
free -h

# Vérifier les processus Python actifs
ps aux | grep python | grep -E "(daily_scraper|main\.py)"

# Vérifier la connectivité vers anime-sama.fr
ping -c 3 anime-sama.fr
```

### 🔄 Automatisation de la surveillance

#### Ajouter une tâche cron pour surveillance automatique
```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour vérifier toutes les heures
0 * * * * /path/to/AnimeSamaScrapper/monitor_service.sh --restart >> /var/log/anime_sama_monitor.log 2>&1

# Ou surveillance complète 4 fois par jour
0 6,12,18,0 * * * /path/to/AnimeSamaScrapper/monitor_service.sh --detailed --restart --email >> /var/log/anime_sama_monitor.log 2>&1
```

#### Script de nettoyage automatique des logs
```bash
# Créer un script de nettoyage
cat > cleanup_logs.sh << 'EOF'
#!/bin/bash
# Nettoyage automatique des logs anciens
find logs/ -name "*.log" -mtime +30 -exec gzip {} \;
find logs/ -name "*.log.gz" -mtime +90 -delete
journalctl --vacuum-time=30d
echo "Nettoyage des logs terminé: $(date)"
EOF

chmod +x cleanup_logs.sh

# Ajouter au cron (une fois par semaine)
# 0 2 * * 0 /path/to/AnimeSamaScrapper/cleanup_logs.sh >> /var/log/cleanup.log 2>&1
```

## 🛠️ Processus complet du scraping

Le script effectue maintenant les étapes suivantes :
1. ✅ Scrape la liste des mangas depuis anime-sama.fr
2. ✅ Parse les métadonnées de chaque manga
3. ✅ Récupère les informations des chapitres via episodes.js
4. ✅ Compte les pages de chaque chapitre
5. ✅ Met à jour la base de données MongoDB
6. ✅ Génère des logs détaillés avec statistiques

## 📊 Métriques et rapports

### Logs détaillés disponibles
- Nombre de mangas traités
- Nombre de chapitres scrapés
- Total de pages comptabilisées
- Durée du processus
- Erreurs et avertissements
- État de la base de données

### Commandes de statistiques
```bash
# Statistiques générales du scraping
python add_to_db.py

# Logs des dernières exécutions
grep "STATISTIQUES FINALES" logs/anime_sama_scraper_*.log | tail -5

# Performance du scraping
grep "Durée totale" logs/anime_sama_scraper_*.log | tail -10
```

## 🚨 Dépannage

### Problèmes courants et solutions

#### 1. Service qui ne démarre pas
```bash
# Vérifier les logs systemd
journalctl -u anime-sama-scraper --no-pager

# Vérifier la configuration du service
sudo systemctl cat anime-sama-scraper

# Tester manuellement
python daily_scraper.py --now
```

#### 2. Erreurs de connexion MongoDB
```bash
# Tester la connexion
python daily_scraper.py --test-db

# Vérifier les variables d'environnement
cat .env

# Tester avec mongosh/mongo client
mongosh "$MONGO_URL"
```

#### 3. Erreurs de scraping
```bash
# Vérifier la connectivité
curl -I https://anime-sama.fr

# Tester le scraping manuel
python main.py

# Analyser les logs d'erreur
grep "ERROR" logs/anime_sama_scraper_*.log | tail -20
```

#### 4. Performance lente
```bash
# Vérifier l'usage des ressources
htop

# Analyser les temps de réponse
grep "Durée" logs/anime_sama_scraper_*.log | tail -10

# Vérifier l'espace disque
df -h
```

## 📈 Résumé des améliorations

Avec ces améliorations, le système AnimeSamaScraper est maintenant :
- 🐧 **100% Linux** - Déploiement et maintenance natifs
- 📖 **Complet** - Comptage précis des pages pour chaque chapitre
- 📊 **Statistiques riches** - Métriques complètes (mangas, chapitres, pages)
- 🔄 **Automatisé** - Service systemd + scripts de maintenance
- 💾 **Robuste** - Stockage structuré MongoDB avec gestion d'erreurs
- 📈 **Monitoré** - Surveillance continue et alertes automatiques
- 🛠️ **Maintenable** - Scripts de mise à jour et diagnostic intégrés

Le système est maintenant **prêt pour la production** avec une maintenance automatisée ! ✅
