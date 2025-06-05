#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de téléchargement des pages de manga depuis MongoDB
Télécharge toutes les pages d'un manga et les compresse en 7z avec conversion WebP
"""

import os
import sys
import py7zr
import requests
import pymongo
from pathlib import Path
from urllib.parse import urlparse
import time
from datetime import datetime
import dotenv
from PIL import Image
import io

# Charger les variables d'environnement
dotenv.load_dotenv()

# Configuration MongoDB
URL = os.getenv("MONGO_URL")
if not URL:
    print("Erreur: Variable d'environnement MONGO_URL non trouvée.")
    print("Veuillez créer un fichier .env avec MONGO_URL=votre_url_mongodb")
    sys.exit(1)

# Connexion MongoDB
try:
    client = pymongo.MongoClient(URL)
    db = client.get_database()
    chapters_collection = db["chapters"]
    mangas_collection = db["mangas"]
    print("Connexion à MongoDB réussie.")
except Exception as e:
    print(f"Erreur de connexion à MongoDB: {e}")
    sys.exit(1)

# Configuration de téléchargement
DOWNLOAD_DIR = "manga_downloads"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def create_download_directory():
    """Crée le dossier de téléchargement s'il n'existe pas"""
    Path(DOWNLOAD_DIR).mkdir(exist_ok=True)
    return DOWNLOAD_DIR

def get_manga_by_title(title):
    """
    Recherche un manga dans la base de données par titre
    
    Args:
        title (str): Titre du manga à rechercher
        
    Returns:
        dict: Document du manga trouvé ou None
    """
    try:
        # Recherche exacte d'abord
        manga = mangas_collection.find_one({"title": title})
        if manga:
            return manga
        
        # Recherche approximative si pas trouvé
        regex_query = {"title": {"$regex": title, "$options": "i"}}
        results = list(mangas_collection.find(regex_query).limit(5))
        
        if not results:
            print(f"Aucun manga trouvé pour '{title}'")
            return None
        
        if len(results) == 1:
            return results[0]
        
        # Afficher les options si plusieurs résultats
        print(f"\nPlusieurs mangas trouvés pour '{title}':")
        for idx, manga in enumerate(results, 1):
            print(f"{idx}. {manga['title']}")
        
        while True:
            try:
                choice = int(input(f"\nChoisissez un manga (1-{len(results)}): ")) - 1
                if 0 <= choice < len(results):
                    return results[choice]
                else:
                    print("Choix invalide.")
            except ValueError:
                print("Veuillez entrer un nombre valide.")
                
    except Exception as e:
        print(f"Erreur lors de la recherche du manga: {e}")
        return None

def get_chapters_for_manga(manga_title, scan_name=None):
    """
    Récupère tous les chapitres d'un manga
    
    Args:
        manga_title (str): Titre du manga
        scan_name (str, optional): Nom du scan spécifique
        
    Returns:
        list: Liste des chapitres
    """
    try:
        query = {"manga_title": manga_title}
        if scan_name:
            query["scan_name"] = scan_name
        
        chapters = list(chapters_collection.find(query).sort("number", 1))
        return chapters
    except Exception as e:
        print(f"Erreur lors de la récupération des chapitres: {e}")
        return []

def download_image(url, filepath, max_retries=3, convert_to_webp=True, webp_quality=60):
    """
    Télécharge une image avec gestion des erreurs et retry, et la convertit en WebP
    
    Args:
        url (str): URL de l'image
        filepath (str): Chemin de destination
        max_retries (int): Nombre maximum de tentatives
        convert_to_webp (bool): Convertir en WebP pour réduire la taille
        webp_quality (int): Qualité WebP (0-100) - 60 pour compression agressive
        
    Returns:
        bool: True si téléchargement réussi, False sinon
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            if convert_to_webp:
                # Convertir l'image en WebP
                try:                    # Charger l'image depuis les bytes
                    image = Image.open(io.BytesIO(response.content))
                    
                    # Redimensionner l'image si elle est trop grande (max 1920x1080 pour économiser l'espace)
                    max_width, max_height = 1920, 1080
                    if image.width > max_width or image.height > max_height:
                        # Calculer le ratio pour maintenir les proportions
                        ratio = min(max_width / image.width, max_height / image.height)
                        new_size = (int(image.width * ratio), int(image.height * ratio))
                        image = image.resize(new_size, Image.Resampling.LANCZOS)
                        print(f"      📏 Redimensionné: {image.width}x{image.height} → {new_size[0]}x{new_size[1]}")
                    
                    # Convertir en RGB si nécessaire (pour éviter les erreurs avec certains formats)
                    if image.mode in ('RGBA', 'LA', 'P'):
                        # Créer un fond blanc pour les images avec transparence
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        if image.mode == 'P':
                            image = image.convert('RGBA')
                        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                        image = background
                    elif image.mode != 'RGB':
                        image = image.convert('RGB')
                    
                    # Changer l'extension en .webp
                    filepath_webp = os.path.splitext(filepath)[0] + '.webp'
                    
                    # Sauvegarder en WebP avec compression
                    image.save(filepath_webp, 'WEBP', quality=webp_quality, optimize=True)
                    
                    # Afficher la réduction de taille
                    original_size = len(response.content)
                    webp_size = os.path.getsize(filepath_webp)
                    reduction = (1 - webp_size / original_size) * 100
                    
                    if reduction > 0:
                        print(f"      💾 WebP: {original_size//1024}KB → {webp_size//1024}KB (-{reduction:.1f}%)")
                    
                    return True
                    
                except Exception as e:
                    print(f"      ⚠️ Erreur conversion WebP: {e}")
                    # Fallback: sauvegarder l'image originale
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    return True
            else:
                # Sauvegarder l'image originale
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"    Échec tentative {attempt + 1}, retry dans 2s... ({e})")
                time.sleep(2)
            else:
                print(f"    Échec définitif après {max_retries} tentatives: {e}")
                return False
        except Exception as e:
            print(f"    Erreur inattendue: {e}")
            return False

def get_image_extension(url):
    """
    Détermine l'extension de fichier à partir de l'URL
    
    Args:
        url (str): URL de l'image
        
    Returns:
        str: Extension du fichier
    """
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    if path.endswith(('.jpg', '.jpeg')):
        return '.jpg'
    elif path.endswith('.png'):
        return '.png'
    elif path.endswith('.gif'):
        return '.gif'
    elif path.endswith('.webp'):
        return '.webp'
    else:
        return '.jpg'  # Par défaut

def download_chapter(chapter, temp_dir):
    """
    Télécharge toutes les pages d'un chapitre
    
    Args:
        chapter (dict): Document du chapitre
        temp_dir (str): Dossier temporaire de téléchargement
        
    Returns:
        list: Liste des fichiers téléchargés
    """
    downloaded_files = []
    
    if 'image_urls' not in chapter:
        print(f"  Chapitre {chapter['number']}: Pas d'URLs d'images disponibles")
        return downloaded_files
    
    image_urls = chapter['image_urls']
    print(f"  Téléchargement de {len(image_urls)} pages...")
    for page_num, url in enumerate(image_urls, 1):
        # Déterminer l'extension (sera changée en .webp lors du téléchargement)
        ext = get_image_extension(url)
        
        # Nom du fichier avec zéro padding (l'extension sera changée en .webp automatiquement)
        filename = f"page_{page_num:03d}{ext}"
        filepath = os.path.join(temp_dir, filename)
        
        print(f"    Page {page_num:3d}/{len(image_urls)}: {filename}")
        
        if download_image(url, filepath):
            # Ajouter le fichier réellement créé (qui pourrait être en .webp)
            webp_filepath = os.path.splitext(filepath)[0] + '.webp'
            if os.path.exists(webp_filepath):
                downloaded_files.append(webp_filepath)
            else:
                downloaded_files.append(filepath)
        else:
            print(f"    ⚠️ Échec du téléchargement de la page {page_num}")
    
    return downloaded_files

def create_7z_archive(source_dir, archive_path, manga_title, scan_name):
    """
    Crée une archive 7z des fichiers téléchargés
    
    Args:
        source_dir (str): Dossier source contenant les fichiers
        archive_path (str): Chemin de l'archive 7z à créer
        manga_title (str): Titre du manga
        scan_name (str): Nom du scan
    """
    try:
        total_files = 0
        total_size = 0
        
        with py7zr.SevenZipFile(archive_path, 'w') as archive:
            # Parcourir tous les chapitres
            for chapter_dir in sorted(os.listdir(source_dir)):
                chapter_path = os.path.join(source_dir, chapter_dir)
                if os.path.isdir(chapter_path):
                    # Ajouter toutes les images du chapitre
                    for filename in sorted(os.listdir(chapter_path)):
                        file_path = os.path.join(chapter_path, filename)
                        # Chemin dans l'archive: Chapitre_X/page_001.webp
                        archive_path_in_7z = f"{chapter_dir}/{filename}"
                        archive.write(file_path, archive_path_in_7z)
                        
                        # Calculer les statistiques
                        total_files += 1
                        total_size += os.path.getsize(file_path)
        
        # Afficher la taille du fichier créé
        archive_size = os.path.getsize(archive_path)
        compression_ratio = (1 - archive_size / total_size) * 100 if total_size > 0 else 0
        
        print(f"\n✅ Archive 7z créée: {archive_path}")
        print(f"📁 Taille originale: {total_size / (1024*1024):.2f} MB")
        print(f"📦 Taille 7z: {archive_size / (1024*1024):.2f} MB")
        print(f"🗜️ Compression 7z: -{compression_ratio:.1f}%")
        print(f"📄 Nombre de fichiers: {total_files}")
        
    except Exception as e:
        print(f"Erreur lors de la création de l'archive 7z: {e}")

def download_manga_complete(manga_title):
    """
    Télécharge toutes les pages d'un manga et les compresse en 7z
    
    Args:
        manga_title (str): Titre du manga à télécharger
    """
    print(f"\n🔍 Recherche du manga: {manga_title}")
    
    # Rechercher le manga
    manga = get_manga_by_title(manga_title)
    if not manga:
        return
    
    manga_title = manga['title']  # Utiliser le titre exact
    print(f"📚 Manga trouvé: {manga_title}")
    
    # Récupérer tous les chapitres
    print("🔍 Recherche des chapitres disponibles...")
    chapters = get_chapters_for_manga(manga_title)
    
    if not chapters:
        print("Aucun chapitre trouvé pour ce manga.")
        return
    
    # Grouper par scan_name
    scans_dict = {}
    for chapter in chapters:
        scan_name = chapter.get('scan_name', 'Unknown')
        if scan_name not in scans_dict:
            scans_dict[scan_name] = []
        scans_dict[scan_name].append(chapter)
    
    print(f"📖 {len(chapters)} chapitres trouvés dans {len(scans_dict)} scans:")
    for scan_name, scan_chapters in scans_dict.items():
        print(f"  - {scan_name}: {len(scan_chapters)} chapitres")
    
    # Demander quel scan télécharger
    if len(scans_dict) > 1:
        print("\nScans disponibles:")
        scan_names = list(scans_dict.keys())
        for idx, scan_name in enumerate(scan_names, 1):
            print(f"{idx}. {scan_name} ({len(scans_dict[scan_name])} chapitres)")
        
        while True:
            try:
                choice = int(input(f"\nChoisissez un scan (1-{len(scan_names)}): ")) - 1
                if 0 <= choice < len(scan_names):
                    selected_scan = scan_names[choice]
                    chapters_to_download = scans_dict[selected_scan]
                    break
                else:
                    print("Choix invalide.")
            except ValueError:
                print("Veuillez entrer un nombre valide.")
    else:
        selected_scan = list(scans_dict.keys())[0]
        chapters_to_download = scans_dict[selected_scan]
    
    print(f"\n📥 Téléchargement de {len(chapters_to_download)} chapitres du scan '{selected_scan}'")
    
    # Créer les dossiers
    base_dir = create_download_directory()
    safe_manga_title = "".join(c for c in manga_title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_scan_name = "".join(c for c in selected_scan if c.isalnum() or c in (' ', '-', '_')).strip()
    
    manga_dir = os.path.join(base_dir, f"{safe_manga_title}_{safe_scan_name}")
    Path(manga_dir).mkdir(exist_ok=True)
    
    # Télécharger chapitre par chapitre
    start_time = time.time()
    total_pages = 0
    successful_chapters = 0
    
    for chapter in chapters_to_download:
        chapter_num = chapter['number']
        print(f"\n📖 Chapitre {chapter_num}: {chapter.get('title', '')}")
          # Créer le dossier du chapitre
        chapter_dir = os.path.join(manga_dir, f"Chapitre_{chapter_num}")
        Path(chapter_dir).mkdir(exist_ok=True)
        
        # Télécharger les pages
        downloaded_files = download_chapter(chapter, chapter_dir)
        
        if downloaded_files:
            total_pages += len(downloaded_files)
            successful_chapters += 1
            print(f"  ✅ {len(downloaded_files)} pages téléchargées")
        else:
            print(f"  ❌ Aucune page téléchargée pour ce chapitre")
            # Supprimer le dossier vide
            try:
                os.rmdir(chapter_dir)
            except:
                pass
    
    # Créer l'archive 7z
    if successful_chapters > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_filename = f"{safe_manga_title}_{safe_scan_name}_{timestamp}.7z"
        archive_path = os.path.join(base_dir, archive_filename)
        
        print(f"\n📦 Création de l'archive 7z...")
        create_7z_archive(manga_dir, archive_path, manga_title, selected_scan)
        
        # Nettoyer les fichiers temporaires
        import shutil
        try:
            shutil.rmtree(manga_dir)
            print("🧹 Fichiers temporaires supprimés")
        except Exception as e:
            print(f"⚠️ Erreur lors du nettoyage: {e}")
        
        # Statistiques finales
        elapsed_time = time.time() - start_time
        print(f"\n📊 Téléchargement terminé:")
        print(f"  - Chapitres: {successful_chapters}/{len(chapters_to_download)}")
        print(f"  - Pages: {total_pages}")
        print(f"  - Temps: {elapsed_time:.1f} secondes")
        print(f"  - Archive: {archive_filename}")
    
    else:
        print("\n❌ Aucun chapitre n'a pu être téléchargé.")

def list_available_mangas():
    """Affiche la liste des mangas disponibles dans la base de données"""
    try:
        print("\n📚 Mangas disponibles dans la base de données:")
        mangas = list(mangas_collection.find({}, {"title": 1, "type": 1, "total_chapters": 1}).sort("title", 1))
        
        for idx, manga in enumerate(mangas, 1):
            title = manga.get('title', 'Sans titre')
            manga_type = manga.get('type', 'N/A')
            total_chapters = manga.get('total_chapters', 0)
            print(f"{idx:3d}. {title} ({manga_type}) - {total_chapters} chapitres")
        
        print(f"\nTotal: {len(mangas)} mangas")
        return mangas
        
    except Exception as e:
        print(f"Erreur lors de la récupération des mangas: {e}")
        return []

def main():
    """Fonction principale avec menu interactif"""
    print("🎌 Téléchargeur de Manga depuis MongoDB")
    print("=" * 50)
    print("💾 Conversion automatique en WebP + Compression 7z")
    print()
    
    # Variable pour test rapide (modifiez cette ligne pour tester un manga spécifique)
    titre_test = "One Piece"  # Changez ce titre pour tester différents mangas
    
    while True:
        print("\nOptions:")
        print("1. Télécharger un manga spécifique")
        print("2. Lister tous les mangas disponibles")
        print(f"3. Test rapide avec '{titre_test}'")
        print("4. Quitter")
        
        choice = input("\nEntrez votre choix (1-4): ").strip()
        
        if choice == "1":
            titre = input("\nEntrez le titre du manga à télécharger: ").strip()
            if titre:
                download_manga_complete(titre)
            else:
                print("Titre invalide.")
        
        elif choice == "2":
            mangas = list_available_mangas()
            if mangas:
                try:
                    choice_num = int(input(f"\nChoisir un manga (1-{len(mangas)}) ou 0 pour revenir: "))
                    if 1 <= choice_num <= len(mangas):
                        selected_manga = mangas[choice_num - 1]
                        download_manga_complete(selected_manga['title'])
                    elif choice_num != 0:
                        print("Choix invalide.")
                except ValueError:
                    print("Veuillez entrer un nombre valide.")
        
        elif choice == "3":
            print(f"\n🚀 Test rapide avec '{titre_test}'")
            download_manga_complete(titre_test)
        
        elif choice == "4":
            print("Au revoir! 👋")
            break
        
        else:
            print("Option invalide. Veuillez choisir entre 1 et 4.")

if __name__ == "__main__":
    main()
