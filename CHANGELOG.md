# CHANGELOG - AnimeSamaScrapper

## Version 2.1.0 - Suppression du scrapping d'images (16 juin 2025)

### 🔄 Changements majeurs

**Suppression du scrapping des images de chapitre :**
- Retrait du Pattern 4 dans `parse_episodes_js()` qui extrayait les URLs d'images
- Suppression de la sauvegarde des `image_urls` et `page_count` dans la base de données MongoDB
- Conservation uniquement des informations relatives au manga (titre, numéro de chapitre, reader_path)

**Fichiers modifiés :**
- `main.py` : Suppression du Pattern 4 (lignes ~538-565)
- `add_to_db.py` : Retrait de la logique de sauvegarde des `image_urls`
- `README.md` : Mise à jour de la documentation pour refléter les changements

**Impact :**
- Le projet ne récupère plus les URLs des images individuelles des chapitres
- Focus exclusif sur les métadonnées des mangas et informations de base des chapitres
- Réduction de la complexité et de la charge sur les serveurs

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
