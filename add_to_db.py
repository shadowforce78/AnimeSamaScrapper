import pymongo
import dotenv
import os
import json
from datetime import datetime
import sys

# Charger les variables d'environnement
dotenv.load_dotenv()

# Obtenir l'URL de connexion MongoDB depuis les variables d'environnement
URL = os.getenv("MONGO_URL")

# Se connecter au cluster MongoDB
client = pymongo.MongoClient(URL)

# Sélectionner la base de données SushiScan (déjà définie dans l'URL)
db = client.get_database()

# Définir les collections
mangas_collection = db["mangas"]  # Stocke les informations de base des mangas
chapters_collection = db["chapters"]  # Stocke les chapitres individuels


def get_data(jsonfile):
    """
    Fonction pour récupérer les données d'un fichier JSON et les insérer dans la base de données MongoDB.

    Args:
        jsonfile (str): Chemin vers le fichier JSON contenant les données des mangas

    Returns:
        tuple: (nb_mangas, nb_chapters) - Nombre de mangas et chapitres ajoutés
    """
    try:
        print(f"Chargement des données depuis {jsonfile}...")
        with open(jsonfile, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"Fichier JSON chargé avec succès. {len(data)} mangas trouvés.")
        return data
    except Exception as e:
        print(f"Erreur lors du chargement du fichier JSON: {e}")
        return None


def insert_mangas_to_db(data):
    """
    Insère les données des mangas dans MongoDB de manière optimisée.

    Args:
        data (list): Liste des données de mangas à insérer

    Returns:
        tuple: (nb_mangas_added, nb_chapters_added) - Nombre de mangas et chapitres ajoutés
    """
    if not data:
        print("Aucune donnée à insérer.")
        return 0, 0

    nb_mangas_added = 0
    nb_chapters_added = 0

    try:
        # Création d'un index sur le titre pour accélérer les recherches
        mangas_collection.create_index([("title", pymongo.ASCENDING)], unique=True)

        # Traitement de chaque manga
        for manga in data:
            # Extraction des chapitres pour insertion séparée
            chapters_data = []
            scan_chapters_copy = []  # Copie pour conserver les données originales

            if "scan_chapters" in manga:
                scan_chapters = manga["scan_chapters"]  # Ne pas utiliser pop() ici

                for scan_type in scan_chapters:
                    # Faire une copie du scan_type pour le manga_doc
                    scan_type_copy = scan_type.copy()

                    if "chapters" in scan_type:
                        chapters = scan_type["chapters"]

                        # Préparation des chapitres pour insertion
                        for chapter in chapters:
                            chapter_doc = {
                                "manga_title": manga["title"],
                                "scan_name": scan_type["name"],
                                "number": chapter["number"],
                                "title": chapter["title"],
                                "page_count": chapter.get("page_count", 0),
                                "scan_id": scan_type.get("id_scan"),
                                "episodes_url": scan_type.get("episodes_url"),
                                "added_at": datetime.now(),
                                "updated_at": datetime.now(),
                            }

                            # Ajout du chemin du reader (compatibilité)
                            if "reader_path" in chapter:
                                chapter_doc["reader_path"] = chapter["reader_path"]

                            chapters_data.append(chapter_doc)

                        # Mettre le count des chapitres dans la copie
                        scan_type_copy["chapters_count"] = len(chapters)
                        # Retirer les chapitres détaillés de la copie pour éviter la duplication
                        scan_type_copy.pop("chapters", None)

                    scan_chapters_copy.append(scan_type_copy)
            # Insertion ou mise à jour des chapitres en premier pour pouvoir calculer les totaux
            if chapters_data:
                # Création d'un index pour rechercher les chapitres
                chapters_collection.create_index(
                    [
                        ("manga_title", pymongo.ASCENDING),
                        ("scan_name", pymongo.ASCENDING),
                        ("number", pymongo.ASCENDING),
                    ],
                    unique=True,
                )

                # Insertion ou mise à jour des chapitres
                for chapter in chapters_data:
                    try:
                        result = chapters_collection.update_one(
                            {
                                "manga_title": chapter["manga_title"],
                                "scan_name": chapter["scan_name"],
                                "number": chapter["number"],
                            },
                            {"$set": chapter},
                            upsert=True,
                        )

                        if result.upserted_id:
                            nb_chapters_added += 1
                    except Exception as e:
                        print(
                            f"Erreur lors de l'insertion du chapitre {chapter['number']} de {chapter['manga_title']}: {e}"
                        )

            # Calculer les totaux depuis la base de données
            manga_title = manga["title"]

            # Compter le nombre de chapitres pour ce manga
            total_chapters = chapters_collection.count_documents(
                {"manga_title": manga_title}
            )

            # Calculer le total de pages pour ce manga
            pipeline_pages = [
                {"$match": {"manga_title": manga_title}},
                {"$group": {"_id": None, "total_pages": {"$sum": "$page_count"}}},
            ]
            page_result = list(chapters_collection.aggregate(pipeline_pages))
            total_pages = page_result[0]["total_pages"] if page_result else 0

            # Ajout des métadonnées du manga avec les totaux corrects
            manga_doc = {
                "title": manga["title"],
                "alt_title": manga.get("alt_title", ""),
                "url": manga["url"],
                "image_url": manga.get("image_url", ""),
                "genres": manga.get("genres", []),
                "type": manga.get("type", ""),
                "language": manga.get("language", ""),
                "scan_types": manga.get("scan_types", []),
                "scan_chapters": scan_chapters_copy,  # Utiliser la copie modifiée
                "total_chapters": total_chapters,
                "total_pages": total_pages,
                "updated_at": datetime.now(),
            }

            # Insertion ou mise à jour du manga (upsert)
            try:
                result = mangas_collection.update_one(
                    {"title": manga["title"]}, {"$set": manga_doc}, upsert=True
                )

                if result.upserted_id:
                    nb_mangas_added += 1
                    print(
                        f"Manga ajouté: {manga['title']} ({total_chapters} chapitres, {total_pages} pages)"
                    )
                else:
                    print(
                        f"Manga mis à jour: {manga['title']} ({total_chapters} chapitres, {total_pages} pages)"
                    )

            except Exception as e:
                print(f"Erreur lors de l'insertion du manga {manga['title']}: {e}")

        return nb_mangas_added, nb_chapters_added

    except Exception as e:
        print(f"Erreur lors de l'insertion en base de données: {e}")
        return 0, 0


def test_connection():
    """
    Teste la connexion à la base de données MongoDB.

    Returns:
        bool: True si la connexion est établie avec succès, False sinon
    """
    try:
        # Vérifier la connexion en listant les collections
        collections = db.list_collection_names()
        print(
            f"Connexion à MongoDB réussie. Collections disponibles: {', '.join(collections)}"
        )
        return True
    except Exception as e:
        print(f"Erreur de connexion à MongoDB: {e}")
        return False


def get_manga_stats():
    """
    Affiche des statistiques sur les mangas et chapitres stockés dans la base de données.
    """
    try:
        manga_count = mangas_collection.count_documents({})
        chapter_count = chapters_collection.count_documents({})

        print(f"\nStatistiques MongoDB:")
        print(f"- Nombre de mangas: {manga_count}")
        print(f"- Nombre de chapitres: {chapter_count}")
        # Top 5 des mangas avec le plus de chapitres
        pipeline = [
            {
                "$group": {
                    "_id": "$manga_title",
                    "chapter_count": {"$sum": 1},
                    "total_pages": {"$sum": "$page_count"},
                }
            },
            {"$sort": {"chapter_count": -1}},
            {"$limit": 5},
        ]

        top_mangas = list(chapters_collection.aggregate(pipeline))

        if top_mangas:
            print("\nTop 5 des mangas avec le plus de chapitres:")
            for idx, manga in enumerate(top_mangas, 1):
                pages_info = (
                    f" ({manga.get('total_pages', 0)} pages)"
                    if manga.get("total_pages", 0) > 0
                    else ""
                )
                print(
                    f"{idx}. {manga['_id']} - {manga['chapter_count']} chapitres{pages_info}"
                )

        # Statistiques sur les pages
        pipeline_pages = [
            {
                "$group": {
                    "_id": None,
                    "total_pages": {"$sum": "$page_count"},
                    "avg_pages_per_chapter": {"$avg": "$page_count"},
                }
            },
        ]

        page_stats = list(chapters_collection.aggregate(pipeline_pages))
        if page_stats:
            stats = page_stats[0]
            print(f"\nStatistiques des pages:")
            print(f"- Nombre total de pages: {stats.get('total_pages', 0)}")
            print(
                f"- Moyenne de pages par chapitre: {stats.get('avg_pages_per_chapter', 0):.1f}"
            )

    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques: {e}")


def search_manga(query):
    """
    Recherche un manga dans la base de données par titre.

    Args:
        query (str): Le titre ou partie du titre à rechercher
    """
    try:
        # Recherche avec une expression régulière (insensible à la casse)
        regex_query = {"title": {"$regex": query, "$options": "i"}}
        results = list(
            mangas_collection.find(
                regex_query,
                {
                    "title": 1,
                    "genres": 1,
                    "type": 1,
                    "total_chapters": 1,
                    "total_pages": 1,
                },
            )
        )

        if results:
            print(f"\nRésultats de recherche pour '{query}' ({len(results)} trouvés):")
            for idx, manga in enumerate(results, 1):
                chapters_info = f" - {manga.get('total_chapters', 0)} chapitres"
                pages_info = (
                    f" ({manga.get('total_pages', 0)} pages)"
                    if manga.get("total_pages", 0) > 0
                    else ""
                )
                print(
                    f"{idx}. {manga['title']} - {manga.get('type', 'N/A')}{chapters_info}{pages_info} - Genres: {', '.join(manga.get('genres', ['N/A']))}"
                )
        else:
            print(f"Aucun manga trouvé pour la recherche '{query}'")

    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")


# Point d'entrée du script
if __name__ == "__main__":
    print("=== Outil d'ajout à la base de données MongoDB ===")

    # Tester la connexion à la base de données
    if not test_connection():
        print(
            "Impossible de se connecter à la base de données. Vérifiez votre connexion et vos identifiants."
        )
        sys.exit(1)
    # Menu principal
    while True:
        print("\nOptions:")
        print("1. Ajouter/mettre à jour depuis anime_data.json")
        print("2. Afficher les statistiques de la base de données")
        print("3. Rechercher un manga par titre")
        print("4. Quitter")

        choice = input("\nEntrez votre choix (1-4): ")

        if choice == "1":
            # Importer les données depuis le fichier JSON
            json_file = "anime_data.json"
            data = get_data(json_file)

            if data:
                print(f"\nAjout de {len(data)} mangas à la base de données...")
                nb_mangas, nb_chapters = insert_mangas_to_db(data)
                print(
                    f"\nOpération terminée. {nb_mangas} nouveaux mangas et {nb_chapters} nouveaux chapitres ajoutés."
                )

                # Afficher un résumé des données ajoutées
                if nb_chapters > 0:
                    # Calculer le total de pages ajoutées
                    total_pages = sum(
                        sum(
                            chapter.get("page_count", 0)
                            for chapter in scan.get("chapters", [])
                        )
                        for manga in data
                        for scan in manga.get("scan_chapters", [])
                    )
                    print(f"Total de pages indexées: {total_pages}")
                    print(
                        f"Moyenne de pages par chapitre: {total_pages/nb_chapters:.1f}"
                        if nb_chapters > 0
                        else "0"
                    )

        elif choice == "2":
            # Afficher les statistiques
            get_manga_stats()

        elif choice == "3":
            # Rechercher un manga
            query = input("Entrez le titre ou une partie du titre à rechercher: ")
            if query.strip():
                search_manga(query)
            else:
                print("Veuillez entrer un terme de recherche valide.")

        elif choice == "4":
            # Quitter
            print("Au revoir!")
            break

        else:
            print("Option invalide. Veuillez choisir entre 1 et 4.")
