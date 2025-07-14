# CHANGELOG - AnimeSamaScrapper

## Version 2.2.0 - Amélioration du comptage des chapitres et des pages (16 juin 2025)

### 🚀 Nouvelles fonctionnalités

**Comptage automatique des chapitres et des pages :**
- Ajout du comptage automatique du nombre total de chapitres par manga
- Ajout du comptage du nombre de pages par chapitre lorsque disponible
- Nouvelle fonction `count_pages_in_chapter()` pour analyser les patterns d'images
- Restauration partielle du Pattern 4 pour détecter les URLs d'images (comptage uniquement, sans stockage)

**Amélioration de la structure des données :**
- La fonction `parse_episodes_js()` retourne maintenant un dictionnaire avec :
  - `total_chapters`: Le nombre total de chapitres
  - `chapters`: Liste des chapitres avec leurs informations détaillées
- Chaque chapitre inclut maintenant le champ `page_count` avec le nombre de pages détectées
- Affichage du nombre total de pages dans les logs de traitement

**Amélioration des patterns de détection :**
- Support amélioré pour différents formats de fichiers episodes.js
- Détection des images indexées : `eps["1"][0] = "image1.jpg";`
- Détection des tableaux d'images : `eps["1"] = ["url1", "url2", ...];`
- Gestion des cas où aucune page n'est détectable (retourne 0)

**Fichiers modifiés :**
- `main.py` : Ajout de `count_pages_in_chapter()` et amélioration de `parse_episodes_js()`
- `main.py` : Mise à jour de `get_scan_chapters()` pour utiliser la nouvelle structure

**Impact sur les données JSON :**
- Structure enrichie avec informations de comptage :
```json
{
  "scan_chapters": [
    {
      "name": "Scan VF",
      "total_chapters": 42,
      "chapters": [
        {
          "number": "1",
          "title": "Chapitre 1",
          "reader_path": "...",
          "page_count": 18
        }
      ]
    }
  ]
}
```

**Compatibilité :**
- Rétrocompatible avec les données existantes
- Gestion gracieuse des cas où le comptage de pages n'est pas possible
- Préservation de toutes les fonctionnalités existantes (conversion Google Drive, etc.)

---

## Version 2.1.0 - Suppression du scrapping d'images (16 juin 2025)

### 🔄 Changements majeurs

**Suppression du scrapping des images de chapitre et des liens de scans :**
- Retrait du Pattern 4 dans `parse_episodes_js()` qui extrayait les URLs d'images
- Suppression de la sauvegarde des `image_urls` et `page_count` dans la base de données MongoDB
- Conservation uniquement des informations relatives au manga (titre, numéro de chapitre, reader_path)
- **Suppression complète du scrapping des liens de scans dans `daily_scraper.py`**

**Fichiers modifiés :**
- `main.py` : Suppression du Pattern 4 (lignes ~538-565)
- `add_to_db.py` : Retrait de la logique de sauvegarde des `image_urls`
- `daily_scraper.py` : Suppression des étapes 4 et 5 (fetch_scan_page_urls et get_scan_chapters)
- `README.md` : Mise à jour de la documentation pour refléter les changements

**Impact :**
- Le projet ne récupère plus les URLs des images individuelles des chapitres
- Le projet ne récupère plus les liens vers les pages de scans
- Focus exclusif sur les métadonnées des mangas du catalogue uniquement
- Réduction significative de la complexité et de la charge sur les serveurs
- Le daily_scraper est maintenant beaucoup plus léger et rapide

---

## Version 2.1.1 - Fix bug chapitres manquants (16 juin 2025)

### 🐛 Corrections importantes

**Résolution du bug des chapitres manquants :**
- **Problème identifié** : Certains chapitres étaient exclus si `page_count <= 0`
- **Solution** : Conservation de TOUS les chapitres détectés, même avec 0 pages
- **Amélioration des regex** : Ajout de patterns supplémentaires pour capturer plus de formats
- **Fonction de diagnostic** : Nouvelle fonction `diagnose_episodes_js()` pour analyser et détecter tous les chapitres possibles
- **Gestion des doublons** : Éviter de traiter plusieurs fois le même chapitre
- **Logs de vérification** : Alertes quand des chapitres sont perdus pendant le parsing

**Exemple** : Chainsaw Man passait de 207 chapitres détectés à seulement 202 chapitres sauvés
→ Maintenant, tous les 207 chapitres sont correctement conservés

**Fichiers modifiés :**
- `main.py` : Refonte complète de `parse_episodes_js()` avec diagnostic
- Ajout de `diagnose_episodes_js()` pour analyse détaillée

---

# Modifications apportées - Conversion des URLs Google Drive

## Résumé des changements

### 1. Nouvelle fonction `convert_google_drive_url()`

Une nouvelle fonction a été ajoutée au fichier `main.py` pour convertir automatiquement les URLs Google Drive de visualisation vers des liens de téléchargement direct.

**Localisation :** Ligne ~430 dans `main.py`

**Fonctionnalité :**
- Détecte les URLs Google Drive dans différents formats
- Extrait l'ID du fichier Google Drive
- Convertit vers le format de téléchargement direct `drive.usercontent.google.com`

**Formats supportés :**
- `https://drive.google.com/uc?export=view&id=ID_FICHIER`
- `https://drive.google.com/file/d/ID_FICHIER/view`
- Recherche générale d'ID avec `id=ID_FICHIER`

### 2. Intégration dans `parse_episodes_js()`

La fonction de conversion a été intégrée dans tous les patterns de parsing des chapitres :

**Pattern 1 :** Conversion des `reader_path`
```python
converted_reader_path = convert_google_drive_url(reader_path)
```

**Pattern 2 :** Conversion des `reader_path` extraits des propriétés
```python
converted_reader_path = convert_google_drive_url(reader_path)
```

**Pattern 3 :** Conversion des `reader_path` du format eps.X
```python
converted_reader_path = convert_google_drive_url(reader_path)
```

### 3. Import ajouté

Ajout de nouveaux imports pour supporter la fonctionnalité :
```python
from urllib.parse import urljoin, urlparse, parse_qs
```

### 4. Correction des problèmes de formatage

- Correction des retours à la ligne manquants dans le code
- Résolution des erreurs de syntaxe Python
- Validation du fichier avec import test

## Impact

### Avantages
1. **Téléchargement direct** : Les URLs convertises permettent un téléchargement direct des images sans passer par l'interface de visualisation Google Drive
2. **Compatibilité améliorée** : Meilleure intégration avec les outils de téléchargement automatique
3. **Performance** : Évite les redirections inutiles lors de l'accès aux fichiers

### Rétrocompatibilité
- Les URLs non-Google Drive restent inchangées
- Gestion d'erreur robuste qui retourne l'URL originale en cas de problème
- Aucun impact sur les fonctionnalités existantes

## Test effectué

Un test de validation a été réalisé pour vérifier le bon fonctionnement de la conversion :

```python
# Exemple de conversion réussie
Original:  https://drive.google.com/uc?export=view&id=1YEdemO6Erm4wt650MoSnjyjw_z05j12W
Converti:  https://drive.usercontent.google.com/download?id=1YEdemO6Erm4wt650MoSnjyjw_z05j12W&export=view&authuser=0
```

## Utilisation

La conversion est automatique et transparente. Lorsque vous exécutez le script `main.py` et récupérez les chapitres (option 4), toutes les URLs Google Drive détectées seront automatiquement converties vers le format de téléchargement direct.

Les données finales dans `anime_data.json` contiendront les URLs converties prêtes à être utilisées pour le téléchargement direct.
