#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour scraper la homepage d'Anime-Sama
Récupère les derniers scans ajoutés, les classiques et les pépites
"""

import requests
import bs4 as bs
import json
import re
import os
from urllib.parse import urljoin
from datetime import datetime

# Configuration
url = "https://anime-sama.fr"
OUTPUT_FILE = "homepage_data.json"

def get_homepage():
    """
    Récupère le contenu HTML de la homepage d'Anime-Sama
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Erreur lors de la récupération de la homepage: {e}")
        return None

def parse_derniers_scans(soup):
    """
    Parse la section 'Derniers scans ajoutés' de la homepage
    """
    derniers_scans = []
    
    # Trouver le conteneur des derniers scans
    container = soup.find("div", id="containerAjoutsScans")
    if not container:
        print("Conteneur 'derniers scans ajoutés' non trouvé")
        return derniers_scans
    
    # Trouver tous les liens directs dans le conteneur
    links = container.find_all("a")
    
    for link in links:
        try:
            scan_data = {}
            
            # URL
            scan_data["url"] = urljoin(url, link.get("href", ""))
            
            # Parent div contenant toutes les infos
            parent_div = link.parent
            
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
                print(f"  Trouvé: {scan_data['title']} - {scan_data.get('latest_chapter', 'N/A')}")
        
        except Exception as e:
            print(f"  Erreur lors du parsing d'un élément de dernier scan: {e}")
            continue
    
    return derniers_scans

def parse_classiques_or_pepites(soup, container_id, section_name):
    """
    Parse les sections 'Classiques' ou 'Pépites' qui ont le même format
    """
    items = []
    
    # Trouver le conteneur
    container = soup.find("div", id=container_id)
    if not container:
        print(f"Conteneur '{section_name}' non trouvé")
        return items
    
    # Trouver tous les éléments - structure réelle avec cartes horizontales
    item_divs = container.find_all("div", class_="shrink-0 m-3 rounded border-2 border-gray-400 border-opacity-50 shadow-2xl shadow-black hover:shadow-zinc-900 hover:opacity-80 bg-black bg-opacity-40 transition-all duration-200 cursor-pointer")
    
    for item_div in item_divs:
        try:
            item_data = {}
            
            # Lien
            link = item_div.find("a")
            if link:
                item_data["url"] = urljoin(url, link.get("href", ""))
            
            # Image
            img = item_div.find("img")
            if img:
                item_data["image_url"] = img.get("src", "")
            
            # Titre
            title_elem = item_div.find("h1")
            if title_elem:
                item_data["title"] = title_elem.get_text(strip=True)
            
            # Titre alternatif (dans le p avec class italic)
            alt_title_elem = item_div.find("p", class_="text-white text-xs opacity-40 truncate italic")
            if alt_title_elem:
                alt_text = alt_title_elem.get_text(strip=True)
                if alt_text:  # Seulement si non vide
                    item_data["alt_title"] = alt_text
            
            # Genres, types et langues (dans les p avec class spécifique)
            info_paragraphs = item_div.find_all("p", class_="mt-0.5 text-gray-300 font-medium text-xs truncate")
            
            if len(info_paragraphs) >= 1:
                # Genres
                genres_text = info_paragraphs[0].get_text(strip=True)
                if genres_text:
                    item_data["genres"] = [genre.strip() for genre in genres_text.split(",")]
            
            if len(info_paragraphs) >= 2:
                # Types (Anime, Scans, etc.)
                types_text = info_paragraphs[1].get_text(strip=True)
                if types_text:
                    item_data["types"] = [t.strip() for t in types_text.split(",")]
            
            if len(info_paragraphs) >= 3:
                # Langues
                languages_text = info_paragraphs[2].get_text(strip=True)
                if languages_text:
                    item_data["languages"] = [lang.strip() for lang in languages_text.split(",")]
            
            if item_data.get("title"):
                items.append(item_data)
                print(f"  Trouvé: {item_data['title']}")
        
        except Exception as e:
            print(f"  Erreur lors du parsing d'un élément de {section_name}: {e}")
            continue
    
    return items

def scrape_homepage():
    """
    Fonction principale pour scraper toute la homepage
    """
    print("=== SCRAPING DE LA HOMEPAGE ANIME-SAMA ===")
    
    # Récupérer le HTML
    print("Récupération de la homepage...")
    html_content = get_homepage()
    if not html_content:
        return None
    
    # Parser le HTML
    soup = bs.BeautifulSoup(html_content, "html.parser")
    
    # Créer la structure de données
    homepage_data = {
        "scraped_at": datetime.now().isoformat(),
        "sections": {}
    }
    
    # 1. Derniers scans ajoutés
    print("\n1. Parsing des derniers scans ajoutés...")
    derniers_scans = parse_derniers_scans(soup)
    homepage_data["sections"]["derniers_scans"] = {
        "title": "Derniers scans ajoutés",
        "count": len(derniers_scans),
        "items": derniers_scans
    }
    print(f"   -> {len(derniers_scans)} derniers scans trouvés")
    
    # 2. Classiques
    print("\n2. Parsing des classiques...")
    classiques = parse_classiques_or_pepites(soup, "containerClassiques", "classiques")
    homepage_data["sections"]["classiques"] = {
        "title": "Les classiques",
        "count": len(classiques),
        "items": classiques
    }
    print(f"   -> {len(classiques)} classiques trouvés")
    
    # 3. Pépites
    print("\n3. Parsing des pépites...")
    pepites = parse_classiques_or_pepites(soup, "containerPepites", "pépites")
    homepage_data["sections"]["pepites"] = {
        "title": "Découvrez des pépites",
        "count": len(pepites),
        "items": pepites
    }
    print(f"   -> {len(pepites)} pépites trouvées")
    
    # Statistiques globales
    total_items = len(derniers_scans) + len(classiques) + len(pepites)
    homepage_data["statistics"] = {
        "total_items": total_items,
        "derniers_scans_count": len(derniers_scans),
        "classiques_count": len(classiques),
        "pepites_count": len(pepites)
    }
    
    print(f"\n=== RÉSUMÉ ===")
    print(f"Total d'éléments scrapés: {total_items}")
    print(f"- Derniers scans: {len(derniers_scans)}")
    print(f"- Classiques: {len(classiques)}")
    print(f"- Pépites: {len(pepites)}")
    
    return homepage_data

def save_homepage_data(data, filename=OUTPUT_FILE):
    """
    Sauvegarde les données dans un fichier JSON
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\nDonnées sauvegardées dans {filename}")
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")
        return False

def display_sample_data(data):
    """
    Affiche un échantillon des données pour vérification
    """
    print("\n=== ÉCHANTILLON DES DONNÉES ===")
    
    for section_key, section_data in data["sections"].items():
        print(f"\n{section_data['title']} ({section_data['count']} éléments):")
        
        # Afficher les 3 premiers éléments de chaque section
        for i, item in enumerate(section_data["items"][:3]):
            print(f"  {i+1}. {item.get('title', 'N/A')}")
            if section_key == "derniers_scans":
                print(f"     Chapitre: {item.get('latest_chapter', 'N/A')}")
                print(f"     Type: {item.get('type', 'N/A')}")
            else:
                if item.get("genres"):
                    print(f"     Genres: {', '.join(item['genres'][:3])}{'...' if len(item['genres']) > 3 else ''}")
                if item.get("types"):
                    print(f"     Types: {', '.join(item['types'])}")
        
        if section_data['count'] > 3:
            print(f"  ... et {section_data['count'] - 3} autres")

if __name__ == "__main__":
    # Scraper la homepage
    homepage_data = scrape_homepage()
    
    if homepage_data:
        # Sauvegarder les données
        save_homepage_data(homepage_data)
        
        # Afficher un échantillon
        display_sample_data(homepage_data)
        
        print(f"\n✅ Scraping terminé avec succès!")
    else:
        print("\n❌ Échec du scraping")
