# 📚 Guide d'utilisation des scripts mis à jour

## 🎯 Résumé des améliorations

Les scripts `add_to_db.py` et `daily_scraper.py` ont été mis à jour pour prendre en charge les nouvelles fonctionnalités de scraping des chapitres et comptage des pages.

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

### Exécution manuelle régulière
Le script s'exécute automatiquement tous les jours à minuit et :
1. ✅ Scrape le catalogue complet
2. ✅ Récupère les types de scan
3. ✅ Analyse tous les fichiers episodes.js
4. ✅ Compte les pages de chaque chapitre
5. ✅ Met à jour la base de données MongoDB
6. ✅ Génère des logs détaillés

## 🎉 Résultats

Avec ces améliorations, vous obtenez maintenant :
- 📖 Comptage précis des pages pour chaque chapitre
- 📊 Statistiques complètes (mangas, chapitres, pages)
- 🔄 Automatisation complète du processus
- 💾 Stockage structuré en base de données
- 📈 Suivi des métriques de contenu

Les scripts sont maintenant **100% opérationnels** pour le scraping complet des données d'Anime-Sama !
