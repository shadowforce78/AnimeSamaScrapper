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
