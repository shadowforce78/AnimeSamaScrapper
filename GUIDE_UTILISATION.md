# 📚 Guide d'utilisation des scripts mis à jour

## 🎯 Résumé des améliorations

Les scripts `add_to_db.py` et `daily_scraper.py` ont été mis à jour pour prendre en charge les nouvelles fonctionnalités de scraping des chapitres et comptage des pages.

## 📁 Scripts disponibles

### 1. `main.py` (Script pri## 🎯 Résumé des améliorations

Avec ces améliorations, vous obtenez maintenant :
- 📖 Comptage précis des pages pour chaque chapitre
- 📊 Statistiques complètes (mangas, chapitres, pages)
- 🔄 Automatisation complète du processus
- 💾 Stockage structuré en base de données
- 📈 Suivi des métriques de contenu
- 🛠️ **Scripts de maintenance automatisés**
- 🔍 **Surveillance continue du service**
- 📧 **Alertes et notifications (extensible)**

### 🚀 Workflow complet de mise à jour
1. **Développement local** → Test avec `python test_updated_scripts.py`
2. **Commit et push** → `git add . && git commit -m "..." && git push`
3. **Mise à jour production** → `.\update_service.ps1 -Backup`
4. **Surveillance** → `.\monitor_service.ps1 -Detailed`

Les scripts sont maintenant **100% opérationnels** pour le scraping complet des données d'Anime-Sama avec maintenance automatisée ! ✅ **Fonctionnalité principale** : Scraping complet des mangas avec comptage des pages
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

## 🚀 Utilisation

### Scraping manuel complet
```bash
# Exécuter le script principal (mode interactif)
python main.py

# Puis suivre les étapes 1→2→3→4 dans le menu
```

### Ajout en base de données
```bash
# Mode interactif
python add_to_db.py

# Sélectionner l'option 1 pour importer depuis anime_data.json
```

### Scraping automatique
```bash
# Test de connexion à la base de données
python daily_scraper.py --test-db

# Exécution immédiate (pour test)
python daily_scraper.py --now

# Mode scheduler (par défaut, s'exécute à minuit)
python daily_scraper.py
```

## 📊 Nouvelles données disponibles

Chaque manga dans `anime_data.json` contient maintenant :

```json
{
  "title": "Nom du manga",
  "scan_chapters": [
    {
      "name": "Scans",
      "total_chapters": 25,
      "chapters": [
        {
          "number": "1",
          "title": "Chapitre 1",
          "page_count": 20,
          "image_urls": ["url1.jpg", "url2.jpg", ...]
        }
      ]
    }
  ]
}
```

## 🗄️ Structure MongoDB

### Collection `mangas`
- Métadonnées des mangas
- **Nouveau** : `total_pages` - Total de pages pour tous les chapitres
- **Nouveau** : `scan_chapters` - Données complètes des scans

### Collection `chapters`
- Chapitres individuels
- **Nouveau** : `page_count` - Nombre de pages du chapitre
- **Nouveau** : `scan_id` - ID du scan source
- **Nouveau** : `episodes_url` - URL du fichier episodes.js
- **Nouveau** : `image_urls` - URLs des images (si disponible)

## 📈 Statistiques disponibles

Le script `add_to_db.py` affiche maintenant :
- Nombre total de mangas et chapitres
- **Nouveau** : Nombre total de pages indexées
- **Nouveau** : Moyenne de pages par chapitre
- Top 5 des mangas avec le plus de chapitres (avec nombre de pages)

## 🔧 Dépendances requises

```bash
pip install pymongo python-dotenv schedule requests beautifulsoup4
```

## 📝 Configuration MongoDB

Créer un fichier `.env` avec :
```
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/database_name
```

## ⚡ Tests

Pour vérifier que tout fonctionne :
```bash
python test_updated_scripts.py
```

## 🕐 Planification automatique

Le `daily_scraper.py` peut être utilisé comme service système :

### Windows (avec le fichier .service fourni)
```bash
# Installer le service
install_service.sh
```

### 🔄 Mise à jour du service après modifications

Quand vous faites des modifications au code et utilisez `git fetch` pour récupérer les dernières versions :

#### Option 1 : Redémarrage complet du service
```bash
# Arrêter le service
net stop AnimeSamaScraper

# Mettre à jour le code
git fetch
git pull

# Redémarrer le service
net start AnimeSamaScraper
```

#### Option 2 : Mise à jour avec réinstallation (recommandé)
```bash
# Arrêter et désinstaller le service
net stop AnimeSamaScraper
sc delete AnimeSamaScraper

# Mettre à jour le code
git fetch
git pull

# Réinstaller le service avec les nouvelles modifications
install_service.sh

# Vérifier que le service fonctionne
net start AnimeSamaScraper
```

#### Option 3 : Script automatisé de mise à jour
Créez un fichier `update_service.bat` :
```batch
@echo off
echo === Mise à jour du service AnimeSamaScraper ===

echo Arrêt du service...
net stop AnimeSamaScraper

echo Mise à jour du code...
git fetch
git pull

echo Redémarrage du service...
net start AnimeSamaScraper

echo === Mise à jour terminée ===
pause
```

#### Vérification après mise à jour
```bash
# Vérifier le statut du service
sc query AnimeSamaScraper

# Consulter les logs pour vérifier le bon fonctionnement
type logs\anime_sama_scraper_%date:~-4%%date:~3,2%%date:~0,2%.log
```

### 📋 Bonnes pratiques pour les mises à jour

1. **Sauvegarde avant mise à jour** :
   ```bash
   # Sauvegarder la base de données
   mongodump --uri="your_mongo_url" --out=backup_before_update
   
   # Sauvegarder les logs
   copy logs logs_backup
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
   Get-Content logs\anime_sama_scraper_*.log -Wait -Tail 10
   ```

### 🔍 Surveillance et maintenance du service

#### Commandes de surveillance essentielles
```powershell
# Vérifier le statut du service
Get-Service AnimeSamaScraper

# Surveiller les logs en temps réel
Get-Content logs\anime_sama_scraper_$(Get-Date -Format 'yyyyMMdd').log -Wait -Tail 10

# Vérifier les dernières exécutions
Get-Content logs\anime_sama_scraper_*.log | Select-String "DÉBUT DU PROCESSUS" | Select-Object -Last 5

# Vérifier les erreurs récentes
Get-Content logs\anime_sama_scraper_*.log | Select-String "ERROR" | Select-Object -Last 10
```

#### Script de monitoring automatique
Créez un fichier `monitor_service.ps1` pour surveillance automatique :
```powershell
# Exécuter toutes les heures pour vérifier le service
$service = Get-Service -Name "AnimeSamaScraper" -ErrorAction SilentlyContinue

if (-not $service -or $service.Status -ne "Running") {
    Write-Host "ALERTE: Service AnimeSamaScraper non fonctionnel" -ForegroundColor Red
    # Ici vous pouvez ajouter une notification par email ou autre
} else {
    Write-Host "Service OK: $($service.Status)" -ForegroundColor Green
}
```

#### Planification de vérifications régulières
```bash
# Ajouter une tâche Windows pour vérifier le service toutes les heures
schtasks /create /tn "AnimeSama Monitor" /tr "powershell.exe -File C:\path\to\monitor_service.ps1" /sc hourly
```

### Exécution manuelle régulière
Le script s'exécute automatiquement tous les jours à minuit et :
1. ✅ Scrape le catalogue complet
2. ✅ Récupère les types de scan
3. ✅ Analyse tous les fichiers episodes.js
4. ✅ Compte les pages de chaque chapitre
5. ✅ Met à jour la base de données MongoDB
6. ✅ Génère des logs détaillés

## 🛠️ Scripts de maintenance fournis

### 📦 Scripts de mise à jour
1. **`update_service.bat`** - Script batch Windows simple
2. **`update_service.ps1`** - Script PowerShell avancé avec options

#### Utilisation du script PowerShell (recommandé)
```powershell
# Mise à jour standard
.\update_service.ps1

# Mise à jour avec sauvegarde automatique
.\update_service.ps1 -Backup

# Mise à jour forcée (ignore les erreurs de tests)
.\update_service.ps1 -Force

# Mise à jour sans exécuter les tests
.\update_service.ps1 -SkipTests

# Mise à jour complète avec toutes les options
.\update_service.ps1 -Backup -Force
```

### 📊 Script de surveillance
**`monitor_service.ps1`** - Surveillance complète du service

```powershell
# Vérification standard
.\monitor_service.ps1

# Vérification détaillée avec tous les logs
.\monitor_service.ps1 -Detailed

# Surveillance avec redémarrage automatique si nécessaire
.\monitor_service.ps1 -RestartIfDown

# Surveillance complète
.\monitor_service.ps1 -Detailed -RestartIfDown
```

### 🔄 Automatisation de la surveillance
```powershell
# Créer une tâche planifiée pour surveiller le service toutes les heures
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\path\to\AnimeSamaScrapper\monitor_service.ps1 -RestartIfDown"
$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365) -Once -At (Get-Date)
Register-ScheduledTask -TaskName "AnimeSama Monitor" -Action $action -Trigger $trigger -Description "Surveillance du service AnimeSamaScraper"
```

## � Résumé des améliorations

Avec ces améliorations, vous obtenez maintenant :
- 📖 Comptage précis des pages pour chaque chapitre
- 📊 Statistiques complètes (mangas, chapitres, pages)
- 🔄 Automatisation complète du processus
- 💾 Stockage structuré en base de données
- 📈 Suivi des métriques de contenu

Les scripts sont maintenant **100% opérationnels** pour le scraping complet des données d'Anime-Sama !
