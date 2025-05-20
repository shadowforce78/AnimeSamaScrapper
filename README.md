# AnimeSamaScrapper

Un outil d'extraction de données pour le site Anime-Sama.fr, spécialisé dans la récupération des mangas, manhwas et leurs chapitres.

## Description

AnimeSamaScrapper est un script Python qui permet d'extraire le catalogue complet des mangas et manhwas disponibles sur Anime-Sama.fr, ainsi que leurs chapitres et pages. Cet outil est particulièrement utile pour les utilisateurs qui souhaitent explorer ou archiver les données du site.

## Fonctionnalités

- Extraction du catalogue complet d'Anime-Sama.fr
- Filtrage des entrées par type (Scans et Manhwa uniquement)
- Identification des différents types de scans disponibles (VF, Spécial VF, etc.)
- Récupération des chapitres disponibles pour chaque manga
- Support de différents formats de fichiers episodes.js

## Prérequis

- Python 3.6 ou supérieur
- Les bibliothèques Python suivantes:
  - requests
  - beautifulsoup4 (bs4)
  - re (regex standard)
  - json
  - os
  - urllib

## Installation

1. Clonez ce dépôt ou téléchargez les fichiers source
2. Installez les dépendances nécessaires:

```bash
pip install -r requirements.txt
```

## Utilisation

### Extraction des données

Exécutez le script principal:

```bash
python main.py
```

Le programme vous présentera un menu interactif avec les options suivantes:

1. **Scraper le catalogue complet** - Récupère toutes les entrées du catalogue Anime-Sama et les filtre par type
2. **Charger des données existantes** - Charge le fichier JSON précédemment enregistré
3. **Récupérer les types de scans** - Pour les entrées chargées, récupère les liens vers les différents types de scans disponibles
4. **Extraire les données des chapitres** - Pour les entrées avec des types de scans, récupère les informations sur les chapitres

Les données extraites sont sauvegardées dans les fichiers suivants:
- `anime_list.html` - HTML brut du catalogue
- `anime_data.json` - Données structurées au format JSON

### Stockage dans MongoDB

Pour stocker les données extraites dans une base de données MongoDB, exécutez le script:

```bash
python add_to_db.py
```

Le script vous présentera un menu interactif avec les options suivantes:

1. **Ajouter/mettre à jour depuis anime_data.json** - Importe les données JSON dans MongoDB
2. **Afficher les statistiques de la base de données** - Montre le nombre de mangas et chapitres stockés
3. **Rechercher un manga par titre** - Permet de rechercher un manga dans la base
4. **Quitter** - Ferme le programme

#### Configuration MongoDB

Pour utiliser MongoDB, assurez-vous d'avoir un fichier `.env` contenant l'URL de connexion:

```
MONGO_URL=mongodb+srv://username:password@hostname/database?retryWrites=true&w=majority
```

Le script utilise la collection `SushiScan` spécifiée dans l'URL de connexion.

## Structure des données

Le fichier JSON généré contient une structure comme celle-ci:

```json
[
  {
    "url": "https://anime-sama.fr/catalogue/...",
    "image_url": "https://anime-sama.fr/assets/images/...",
    "title": "Nom du manga",
    "alt_title": "Nom alternatif",
    "genres": ["Action", "Drama", "..."],
    "type": "Scans",
    "language": "VOSTFR",
    "scan_types": [
      {
        "name": "Scan VF",
        "url": "https://anime-sama.fr/catalogue/..."
      }
    ],
    "scan_chapters": [
      {
        "name": "Scan VF",
        "url": "https://anime-sama.fr/catalogue/...",
        "id_scan": "123456",
        "episodes_url": "https://anime-sama.fr/catalogue/.../episodes.js?filever=123456",
        "total_chapters": 42,
        "chapters": [
          {
            "number": "1",
            "title": "Chapitre 1",
            "reader_path": "reader.php?path=..."
          },
          // ou format avec URLs d'images
          {
            "number": "2",
            "title": "Chapitre 2",
            "image_urls": ["https://...", "https://..."],
            "page_count": 24
          }
        ]
      }
    ]
  }
]
```

## Structure de la base de données MongoDB

Les données extraites peuvent être stockées dans une base de données MongoDB à l'aide du script `add_to_db.py`. La structure de la base de données est organisée pour optimiser les requêtes et l'accès aux données.

### Collection `mangas`

Cette collection stocke les informations générales sur les mangas :

```json
{
  "_id": "ObjectId(...)",
  "title": "Nom du manga",
  "alt_title": "Nom alternatif",
  "url": "https://anime-sama.fr/catalogue/...",
  "image_url": "https://anime-sama.fr/assets/images/...",
  "genres": ["Action", "Drama", "..."],
  "type": "Scans",
  "language": "VOSTFR",
  "scan_types": [
    {
      "name": "Scan VF",
      "url": "https://anime-sama.fr/catalogue/...",
      "chapters_count": 42
    }
  ],
  "updated_at": "2025-05-20T14:30:00.000Z"
}
```

### Collection `chapters`

Cette collection stocke les informations détaillées sur chaque chapitre, avec une référence au manga parent :

```json
{
  "_id": "ObjectId(...)",
  "manga_title": "Nom du manga",
  "scan_name": "Scan VF",
  "number": "1",
  "title": "Chapitre 1",
  "reader_path": "reader.php?path=...",
  "added_at": "2025-05-20T14:30:00.000Z"
}
```

Ou pour les chapitres avec des URLs d'images :

```json
{
  "_id": "ObjectId(...)",
  "manga_title": "Nom du manga",
  "scan_name": "Scan VF",
  "number": "2",
  "title": "Chapitre 2",
  "image_urls": ["https://...", "https://..."],
  "page_count": 24,
  "added_at": "2025-05-20T14:30:00.000Z"
}
```

### Indexation

La base de données utilise plusieurs index pour optimiser les performances :

1. Index unique sur le champ `title` dans la collection `mangas`
2. Index composé unique sur les champs `manga_title`, `scan_name` et `number` dans la collection `chapters`

### Accéder aux données

Exemples de requêtes MongoDB pour accéder aux données :

```javascript
// Rechercher un manga par titre
db.mangas.findOne({ title: "Nom du manga" })

// Obtenir tous les chapitres d'un manga spécifique
db.chapters.find({ manga_title: "Nom du manga" }).sort({ number: 1 })

// Obtenir les chapitres d'un type de scan spécifique
db.chapters.find({ manga_title: "Nom du manga", scan_name: "Scan VF" })

// Trouver un chapitre spécifique
db.chapters.findOne({ 
  manga_title: "Nom du manga", 
  scan_name: "Scan VF", 
  number: "1" 
})
```

## Notes techniques

- Le script supporte plusieurs formats de données dans le fichier episodes.js:
  - Format objet : `eps["1"] = {"r":"reader.php?path=...","t":"Chapitre 1"};`
  - Format tableau : `var eps1= ['url1', 'url2', ...];`
- Plusieurs méthodes de fallback sont implémentées pour gérer les différentes structures de page
- Des délais sont intégrés pour éviter de surcharger le serveur

## Aspects juridiques

Ce script est fourni à des fins éducatives uniquement. Veuillez respecter les conditions d'utilisation du site Anime-Sama.fr et les droits d'auteur des contenus. N'utilisez pas cet outil pour télécharger ou distribuer des contenus protégés sans autorisation.

## Contribution

Les contributions sont les bienvenues! N'hésitez pas à ouvrir une issue ou une pull request pour suggérer des améliorations ou signaler des bugs.

## Licence

[MIT](https://opensource.org/licenses/MIT)
