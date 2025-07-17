#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'intégration du scraper homepage avec MongoDB
"""

import requests
import bs4 as bs
import json
from urllib.parse import urljoin
from datetime import datetime
import os
import sys

# Import des modules du projet
try:
    from add_to_db import get_manga_collection, get_homepage_collection
except ImportError:
    print("Erreur : Impossible d'importer add_to_db. Assurez-vous que le module existe.")
    sys.exit(1)

def scrape_homepage_to_db():
    """
    Scrape la homepage et sauvegarde directement en base
    """
    print("=== SCRAPING HOMEPAGE VERS MONGODB ===")
    
    # Récupérer les données de la homepage
    homepage_data = scrape_homepage_data()
    if not homepage_data:
        print("❌ Impossible de récupérer les données de la homepage")
        return False
    
    # Sauvegarder en base
    try:
        # Récupérer la collection homepage
        homepage_collection = get_homepage_collection()
        
        # Supprimer les anciennes données (optionnel)
        print("Suppression des anciennes données homepage...")
        homepage_collection.delete_many({})
        
        # Insérer les nouvelles données
        print("Insertion des nouvelles données...")
        result = homepage_collection.insert_one(homepage_data)
        
        if result.inserted_id:
            print(f"✅ Données homepage sauvegardées avec l'ID: {result.inserted_id}")
            return True
        else:
            print("❌ Erreur lors de l'insertion en base")
            return False
            
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False

def scrape_homepage_data():
    """
    Fonction principale pour récupérer les données de la homepage
    Retourne les données structurées
    """
    url = "https://anime-sama.fr"
    
    try:
        # Récupérer le HTML
        print("Récupération de la homepage...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parser le HTML
        soup = bs.BeautifulSoup(response.text, "html.parser")
        
        # Créer la structure de données
        homepage_data = {
            "scraped_at": datetime.now().isoformat(),
            "sections": {}
        }
        
        # 1. Derniers scans ajoutés
        print("Parsing des derniers scans ajoutés...")
        derniers_scans = parse_derniers_scans(soup, url)
        homepage_data["sections"]["derniers_scans"] = {
            "title": "Derniers scans ajoutés",
            "count": len(derniers_scans),
            "items": derniers_scans
        }
        print(f"   -> {len(derniers_scans)} derniers scans trouvés")
        
        # 2. Classiques
        print("Parsing des classiques...")
        classiques = parse_classiques_or_pepites(soup, "containerClassiques", "classiques", url)
        homepage_data["sections"]["classiques"] = {
            "title": "Les classiques",
            "count": len(classiques),
            "items": classiques
        }
        print(f"   -> {len(classiques)} classiques trouvés")
        
        # 3. Pépites
        print("Parsing des pépites...")
        pepites = parse_classiques_or_pepites(soup, "containerPepites", "pépites", url)
        homepage_data["sections"]["pepites"] = {
            "title": "Découvrez des pépites",
            "count": len(pepites),
            "items": pepites
        }
        print(f"   -> {len(pepites)} pépites trouvées")
        
        # Statistiques
        total_items = len(derniers_scans) + len(classiques) + len(pepites)
        homepage_data["statistics"] = {
            "total_items": total_items,
            "derniers_scans_count": len(derniers_scans),
            "classiques_count": len(classiques),
            "pepites_count": len(pepites)
        }
        
        print(f"Total d'éléments scrapés: {total_items}")
        return homepage_data
        
    except Exception as e:
        print(f"Erreur lors du scraping: {e}")
        return None

def parse_derniers_scans(soup, base_url):
    """
    Parse la section 'Derniers scans ajoutés' de la homepage
    """
    derniers_scans = []
    
    # Trouver le conteneur des derniers scans
    container = soup.find("div", id="containerAjoutsScans")
    if not container:
        return derniers_scans
    
    # Trouver tous les liens directs dans le conteneur
    links = container.find_all("a")
    
    for link in links:
        try:
            scan_data = {}
            
            # URL
            scan_data["url"] = urljoin(base_url, link.get("href", ""))
            
            # Image
            img = link.find("img")
            if img:
                scan_data["image_url"] = img.get("src", "")
            
            # Titre
            title_elem = link.find("h1")
            if title_elem:
                scan_data["title"] = title_elem.get_text(strip=True)
            
            # Informations dans les boutons (type, langue, chapitre)
            buttons = link.find_all("button")
            scan_data["type"] = ""
            scan_data["language"] = ""
            scan_data["latest_chapter"] = ""
            
            for button in buttons:
                text = button.get_text(strip=True)
                if any(word in text.lower() for word in ["webtoon", "manga", "manhwa"]):
                    scan_data["type"] = text
                elif text in ["FR", "VF", "VOSTFR"]:
                    scan_data["language"] = text
                elif "chapitre" in text.lower():
                    scan_data["latest_chapter"] = text
            
            if scan_data.get("title"):
                derniers_scans.append(scan_data)
        
        except Exception as e:
            continue
    
    return derniers_scans

def parse_classiques_or_pepites(soup, container_id, section_name, base_url):
    """
    Parse les sections 'Classiques' ou 'Pépites' qui ont le même format
    """
    items = []
    
    # Trouver le conteneur
    container = soup.find("div", id=container_id)
    if not container:
        return items
    
    # Trouver tous les éléments - structure réelle avec cartes horizontales
    item_divs = container.find_all("div", class_="shrink-0 m-3 rounded border-2 border-gray-400 border-opacity-50 shadow-2xl shadow-black hover:shadow-zinc-900 hover:opacity-80 bg-black bg-opacity-40 transition-all duration-200 cursor-pointer")
    
    for item_div in item_divs:
        try:
            item_data = {}
            
            # Lien
            link = item_div.find("a")
            if link:
                item_data["url"] = urljoin(base_url, link.get("href", ""))
            
            # Image
            img = item_div.find("img")
            if img:
                item_data["image_url"] = img.get("src", "")
            
            # Titre
            title_elem = item_div.find("h1")
            if title_elem:
                item_data["title"] = title_elem.get_text(strip=True)
            
            # Titre alternatif
            alt_title_elem = item_div.find("p", class_="text-white text-xs opacity-40 truncate italic")
            if alt_title_elem:
                alt_text = alt_title_elem.get_text(strip=True)
                if alt_text:
                    item_data["alt_title"] = alt_text
            
            # Genres, types et langues
            info_paragraphs = item_div.find_all("p", class_="mt-0.5 text-gray-300 font-medium text-xs truncate")
            
            if len(info_paragraphs) >= 1:
                genres_text = info_paragraphs[0].get_text(strip=True)
                if genres_text:
                    item_data["genres"] = [genre.strip() for genre in genres_text.split(",")]
            
            if len(info_paragraphs) >= 2:
                types_text = info_paragraphs[1].get_text(strip=True)
                if types_text:
                    item_data["types"] = [t.strip() for t in types_text.split(",")]
            
            if len(info_paragraphs) >= 3:
                languages_text = info_paragraphs[2].get_text(strip=True)
                if languages_text:
                    item_data["languages"] = [lang.strip() for lang in languages_text.split(",")]
            
            if item_data.get("title"):
                items.append(item_data)
        
        except Exception as e:
            continue
    
    return items

def get_latest_homepage_data():
    """
    Récupère les dernières données de la homepage depuis MongoDB
    """
    try:
        homepage_collection = get_homepage_collection()
        latest_data = homepage_collection.find_one(sort=[("scraped_at", -1)])
        return latest_data
    except Exception as e:
        print(f"Erreur lors de la récupération des données homepage: {e}")
        return None

def display_homepage_stats():
    """
    Affiche les statistiques de la dernière homepage scrapée
    """
    data = get_latest_homepage_data()
    if not data:
        print("Aucune donnée homepage trouvée en base")
        return
    
    print(f"\n=== STATS HOMEPAGE (scrapé le {data['scraped_at']}) ===")
    stats = data.get("statistics", {})
    
    print(f"Total d'éléments: {stats.get('total_items', 0)}")
    print(f"- Derniers scans: {stats.get('derniers_scans_count', 0)}")
    print(f"- Classiques: {stats.get('classiques_count', 0)}")
    print(f"- Pépites: {stats.get('pepites_count', 0)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scraper homepage Anime-Sama")
    parser.add_argument("--action", choices=["scrape", "stats"], default="scrape",
                       help="Action à effectuer: scrape (défaut) ou stats")
    
    args = parser.parse_args()
    
    if args.action == "scrape":
        success = scrape_homepage_to_db()
        if success:
            display_homepage_stats()
    elif args.action == "stats":
        display_homepage_stats()
