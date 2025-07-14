import os
import sys
import json
import time
import logging
from datetime import datetime
import schedule
import requests

# Import des fonctions du script principal
from main import (
    get_anime_list, 
    refine_data, 
    fetch_scan_page_urls,
    get_scan_chapters,
    remove_old_files
)
from add_to_db import insert_mangas_to_db, test_connection, insert_planning_to_db
from planning import scrape_planning

# Configuration du logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"anime_sama_scraper_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("anime_sama_scraper")

# Fichiers temporaires et résultats
ANIME_LIST_HTML_FILE = "anime_list.html"
ANIME_DATA_JSON_FILE = "anime_data.json"

def scrape_and_update_db():
    """
    Fonction principale qui exécute le processus complet de scraping et de mise à jour de la base de données
    Récupère les métadonnées des mangas ET les informations des chapitres (sans les URLs d'images).
    """
    start_time = time.time()
    logger.info("==== DÉBUT DU PROCESSUS DE SCRAPING QUOTIDIEN ====")
    
    try:
        # Étape 1: Tester la connexion à la base de données
        if not test_connection():
            logger.error("Impossible de se connecter à la base de données MongoDB. Arrêt du processus.")
            return False

        # Étape 2: Récupérer le catalogue d'Anime-Sama
        logger.info("Récupération du catalogue d'Anime-Sama...")
        
        # Etape 2.1: Suppression des anciens fichiers
        remove_old_files()
        logger.info("Suppression des anciens fichiers temporaires...")
        
        # Etape 2.2: Scraping du catalogue HTML
        anime_list_html = get_anime_list()
        if not anime_list_html:
            logger.error("Échec de la récupération du catalogue. Arrêt du processus.")
            return False
        
        # Sauvegarde du HTML brut
        with open(ANIME_LIST_HTML_FILE, "w", encoding="utf-8") as file:
            file.write(anime_list_html)
        logger.info(f"HTML du catalogue sauvegardé dans {ANIME_LIST_HTML_FILE}")
        
        # Etape 2.3: Raffinage des données (métadonnées des mangas)
        logger.info("Analyse et filtrage des données du catalogue...")
        refined_anime_data_json_string = refine_data(ANIME_LIST_HTML_FILE)
        if not refined_anime_data_json_string:
            logger.error("Échec du raffinement des données. Arrêt du processus.")
            return False
        
        # Conversion en objet Python
        try:
            anime_data_list = json.loads(refined_anime_data_json_string)
            logger.info(f"Données raffinées avec succès. {len(anime_data_list)} mangas trouvés.")
            
            # Sauvegarde des données raffinées
            with open(ANIME_DATA_JSON_FILE, "w", encoding="utf-8") as json_file_out:
                json.dump(anime_data_list, json_file_out, indent=4, ensure_ascii=False)
            logger.info(f"Données raffinées sauvegardées dans {ANIME_DATA_JSON_FILE}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur lors de la conversion JSON: {e}")
            return False
        
        logger.info("Processus de scraping des métadonnées terminé avec succès.")
        
        # Étape 3: Récupérer les types de scans pour chaque manga/anime
        logger.info("Récupération des types de scans disponibles...")
        anime_data_list = fetch_scan_page_urls(anime_data_list)
        
        # Sauvegarde intermédiaire après récupération des types de scans
        with open(ANIME_DATA_JSON_FILE, "w", encoding="utf-8") as json_file_out:
            json.dump(anime_data_list, json_file_out, indent=4, ensure_ascii=False)
        logger.info("Types de scans récupérés et sauvegardés.")
        
        # Étape 4: Récupérer les chapitres de chaque scan
        logger.info("Récupération des chapitres disponibles...")
        anime_data_list = get_scan_chapters(anime_data_list)
        
        # Sauvegarde finale des données complètes
        with open(ANIME_DATA_JSON_FILE, "w", encoding="utf-8") as json_file_out:
            json.dump(anime_data_list, json_file_out, indent=4, ensure_ascii=False)
        logger.info("Chapitres récupérés et sauvegardés.")
        
        # Étape 5: Préparation des données pour insertion en base
        logger.info("Préparation des données pour insertion en base...")
        
        # Calculer les statistiques avant insertion
        total_chapters = sum(
            sum(scan.get('total_chapters', 0) for scan in manga.get('scan_chapters', []))
            for manga in anime_data_list
        )
        total_pages = sum(
            sum(
                sum(chapter.get('page_count', 0) for chapter in scan.get('chapters', []))
                for scan in manga.get('scan_chapters', [])
            )
            for manga in anime_data_list
        )
        
        logger.info(f"Statistiques des données: {len(anime_data_list)} mangas, {total_chapters} chapitres, {total_pages} pages")
        
        # Étape 6: Insérer ou mettre à jour les données dans MongoDB
        logger.info("Mise à jour de la base de données MongoDB...")
        nb_mangas_added, nb_chapters_added = insert_mangas_to_db(anime_data_list)
        logger.info(f"Base de données mise à jour avec succès:")
        logger.info(f"- {nb_mangas_added} nouveaux mangas ajoutés")
        logger.info(f"- {nb_chapters_added} nouveaux chapitres ajoutés")
        
        # Etape 7: Scraper le planning et l'insérer dans la base de données
        logger.info("Scraping du planning des sorties...")
        planning_data = scrape_planning()
        if planning_data:
            logger.info(f"Planning des sorties récupéré avec succès. {len(planning_data)} entrées trouvées.")
            insert_planning_to_db(planning_data)
            logger.info("Planning inséré dans la base de données avec succès.")
        else:
            logger.warning("Aucune donnée de planning trouvée ou erreur lors du scraping du planning.")
        logger.info("Processus de scraping complet et mise à jour de la base de données terminé avec succès.")
        
        
        # Calculer le temps d'exécution total
        execution_time = time.time() - start_time
        logger.info(f"==== FIN DU PROCESSUS DE SCRAPING ({execution_time:.2f} secondes) ====")
        
        return True
    
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Erreur de connexion lors du scraping: {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue lors du processus de scraping: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return False

def run_scheduled_job():
    """
    Fonction qui sera appelée par le scheduler
    Inclut gestion des erreurs et retries en cas d'échec
    """
    logger.info("Exécution du job planifié...")
    
    # Tentatives en cas d'échec (max 3 essais)
    max_retries = 3
    retry_delay = 300  # 5 minutes
    
    for attempt in range(1, max_retries + 1):
        try:
            success = scrape_and_update_db()
            if success:
                logger.info("Job terminé avec succès.")
                return
            else:
                logger.warning(f"Échec du job (tentative {attempt}/{max_retries})")
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du job (tentative {attempt}/{max_retries}): {e}")
        
        if attempt < max_retries:
            logger.info(f"Nouvelle tentative dans {retry_delay} secondes...")
            time.sleep(retry_delay)
    
    logger.error(f"Toutes les tentatives ont échoué ({max_retries}). Abandon du job.")

def setup_schedule():
    """
    Configure le scheduler pour exécuter le job tous les jours à minuit
    """
    schedule.every().day.at("00:00").do(run_scheduled_job)
    logger.info("Job planifié tous les jours à minuit (00:00)")
    logger.info("Le job comprend le scraping complet: mangas, chapitres et pages (sans URLs d'images)")

def run_once():
    """
    Exécute le job une seule fois immédiatement
    Utile pour les tests ou les exécutions manuelles
    """
    logger.info("Exécution immédiate du job de scraping complet...")
    run_scheduled_job()

def start_scheduler():
    """
    Démarre le scheduler en boucle infinie
    """
    setup_schedule()
    logger.info("Démarrage du scheduler...")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Vérifier le scheduler toutes les minutes

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Script de scraping automatique pour Anime-Sama")
    parser.add_argument("--now", action="store_true", help="Exécuter le scraping complet immédiatement")
    parser.add_argument("--schedule", action="store_true", help="Démarrer le scheduler (par défaut)")
    parser.add_argument("--test-db", action="store_true", help="Tester uniquement la connexion à la base de données")
    
    args = parser.parse_args()
    
    if args.test_db:
        # Test de connexion uniquement
        if test_connection():
            logger.info("Test de connexion réussi !")
            sys.exit(0)
        else:
            logger.error("Test de connexion échoué !")
            sys.exit(1)
    elif args.now:
        # Exécution immédiate
        run_once()
    else:
        # Mode scheduler
        try:
            logger.info("Mode scheduler activé. Le scraping complet sera exécuté quotidiennement à minuit.")
            # Exécuter une première fois au démarrage
            run_scheduled_job()
            # Puis configurer le scheduler
            start_scheduler()
        except KeyboardInterrupt:
            logger.info("Arrêt du scheduler (Ctrl+C)")
            sys.exit(0)
