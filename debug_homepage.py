#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de debug pour analyser la structure de la homepage d'Anime-Sama
"""

import requests
import bs4 as bs

def debug_homepage():
    """
    Analyse la structure de la homepage pour debug
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get("https://anime-sama.fr", headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = bs.BeautifulSoup(response.text, "html.parser")
        
        print("=== DEBUG HOMEPAGE STRUCTURE ===")
        
        # Rechercher les conteneurs par ID
        containers_to_check = [
            "containerAjoutsScans",
            "containerClassiques", 
            "containerPepites"
        ]
        
        for container_id in containers_to_check:
            container = soup.find("div", id=container_id)
            print(f"\n{container_id}: {'TROUVÉ' if container else 'NON TROUVÉ'}")
            
            if container:
                # Compter les éléments enfants
                children = container.find_all("div", recursive=False)
                print(f"  Enfants directs: {len(children)}")
                
                # Chercher différents types de cartes
                cards_type1 = container.find_all("div", class_="relative z-0 flex shrink-0")
                cards_type2 = container.find_all("div", class_="shrink-0 m-3 rounded border-2")
                cards_type3 = container.find_all("a")
                
                print(f"  Cartes type 1 (relative z-0): {len(cards_type1)}")
                print(f"  Cartes type 2 (shrink-0 m-3): {len(cards_type2)}")
                print(f"  Liens directs: {len(cards_type3)}")
        
        # Rechercher par texte pour identifier les sections
        print("\n=== RECHERCHE PAR TEXTE ===")
        sections_text = [
            "Derniers scans ajoutés",
            "derniers scans",
            "Classiques",
            "classiques", 
            "Pépites",
            "pépites"
        ]
        
        for text in sections_text:
            elements = soup.find_all(text=lambda t: t and text.lower() in t.lower())
            print(f"'{text}': {len(elements)} occurrences")
            
            if elements:
                for i, elem in enumerate(elements[:2]):  # Montrer les 2 premiers
                    parent = elem.parent if elem.parent else None
                    print(f"  {i+1}. Parent: {parent.name if parent else 'None'} - Classes: {parent.get('class', []) if parent else 'None'}")
        
        # Rechercher des patterns communs de cartes
        print("\n=== PATTERNS DE CARTES ===")
        common_patterns = [
            ("div[class*='card']", "Cartes avec 'card'"),
            ("div[class*='scan']", "Cartes avec 'scan'"),
            ("div[class*='manga']", "Cartes avec 'manga'"),
            ("div[class*='item']", "Cartes avec 'item'"),
            ("div[class*='flex']", "Divs avec flex"),
            ("img[src*='covers']", "Images de couvertures"),
            ("h1, h2, h3", "Titres"),
        ]
        
        for selector, description in common_patterns:
            elements = soup.select(selector)
            print(f"{description}: {len(elements)} éléments")
            if elements and len(elements) < 20:  # Éviter trop de sortie
                for elem in elements[:3]:
                    print(f"  - {elem.name}: {elem.get('class', [])} - Texte: {elem.get_text(strip=True)[:50]}...")
        
        # Sauvegarder un échantillon du HTML pour analyse
        with open("homepage_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"\nHTML complet sauvegardé dans homepage_debug.html ({len(response.text)} caractères)")
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    debug_homepage()
