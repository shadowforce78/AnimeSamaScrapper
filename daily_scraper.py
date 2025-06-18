#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de scraping automatique pour Anime-Sama
Exécuté quotidiennement à minuit pour mettre à jour la base de données MongoDB
avec les derniers mangas et leurs chapitres/pages disponibles.
"""

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
    process_all_steps_in_order
)
from add_to_db import insert_mangas_to_db, test_connection

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
    Inclut maintenant le scraping des chapitres et comptage des pages.
    """
    start_time = time.time()
    logger.info("==== DÉBUT DU PROCESSUS DE SCRAPING QUOTIDIEN ====")
    
    try:
        # Étape 1: Tester la connexion à la base de données
        if not test_connection():
            logger.error("Impossible de se connecter à la base de données MongoDB. Arrêt du processus.")
            return False

        # Étape 2: Exécuter toutes les étapes de scraping dans l'ordre
        logger.info("Exécution du processus complet de scraping (4 étapes)...")
        
        # Utilise la fonction process_all_steps_in_order du script principal
        # qui exécute les 4 étapes : récupération HTML, raffinage, scan des chapitres, et sauvegarde
        success = process_all_steps_in_order()
        
        if not success:
            logger.error("Échec du processus de scraping. Arrêt du processus.")
            return False
        
        logger.info("Processus de scraping terminé avec succès.")
        
        # Étape 3: Charger les données générées
        logger.info("Chargement des données générées pour insertion en base...")
        try:
            with open(ANIME_DATA_JSON_FILE, 'r', encoding='utf-8') as f:
                anime_data_list = json.load(f)
            logger.info(f"Données chargées avec succès. {len(anime_data_list)} mangas trouvés.")
            
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
            
            logger.info(f"Statistiques des données: {total_chapters} chapitres, {total_pages} pages")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des données: {e}")
            return False
        
        # Étape 4: Insérer ou mettre à jour les données dans MongoDB
        logger.info("Mise à jour de la base de données MongoDB...")
        nb_mangas_added, nb_chapters_added = insert_mangas_to_db(anime_data_list)
        logger.info(f"Base de données mise à jour avec succès:")
        logger.info(f"- {nb_mangas_added} nouveaux mangas ajoutés")
        logger.info(f"- {nb_chapters_added} nouveaux chapitres ajoutés")
        
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
    logger.info("Le job comprend maintenant le scraping complet des chapitres et pages")

def run_once():
    """
    Exécute le job une seule fois immédiatement
    Utile pour les tests ou les exécutions manuelles
    """
    logger.info("Exécution immédiate du job complet (avec scraping des chapitres)...")
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
