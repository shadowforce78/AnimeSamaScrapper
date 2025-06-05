#!/usr/bin/env python3
import pymongo
import dotenv
import os
from urllib.parse import urlparse

# Charger les variables d'environnement
dotenv.load_dotenv()

# Connexion MongoDB
client = pymongo.MongoClient(os.getenv('MONGO_URL'))
db = client.get_database()
chapters_collection = db['chapters']

# Analyser les URLs d'images
print("=== ANALYSE DES URLs D'IMAGES ===\n")

# Trouver un échantillon de chapitres avec des URLs
sample_chapters = list(chapters_collection.find({'image_urls': {'$exists': True}}).limit(3))

if sample_chapters:
    for idx, chapter in enumerate(sample_chapters, 1):
        print(f"Chapitre {idx}: {chapter['manga_title']} - Ch.{chapter['number']}")
        print(f"Nombre d'images: {len(chapter['image_urls'])}")
        
        # Analyser les domaines des URLs
        domains = {}
        for url in chapter['image_urls'][:5]:  # Première 5 URLs seulement
            domain = urlparse(url).netloc
            domains[domain] = domains.get(domain, 0) + 1
            print(f"  - {url}")
        
        print(f"Domaines détectés: {domains}")
        print("-" * 50)

# Statistiques globales sur les domaines
print("\n=== STATISTIQUES GLOBALES ===")
all_chapters = chapters_collection.find({'image_urls': {'$exists': True}})
total_chapters = 0
total_images = 0
domain_stats = {}

for chapter in all_chapters:
    total_chapters += 1
    total_images += len(chapter['image_urls'])
    
    # Analyser quelques URLs du chapitre
    for url in chapter['image_urls'][:2]:  # Seulement 2 URLs par chapitre pour la vitesse
        domain = urlparse(url).netloc
        domain_stats[domain] = domain_stats.get(domain, 0) + 1

print(f"Total chapitres avec images: {total_chapters}")
print(f"Total estimé d'images: {total_images}")
print(f"Domaines utilisés: {domain_stats}")

# Calcul estimé de la taille
average_image_size_mb = 0.5  # Estimation conservative
estimated_total_size_gb = (total_images * average_image_size_mb) / 1024
print(f"\nTaille estimée (images originales): {estimated_total_size_gb:.1f} GB")
print(f"Taille estimée après WebP 60%: {estimated_total_size_gb * 0.3:.1f} GB")
print(f"Taille estimée après 7z: {estimated_total_size_gb * 0.2:.1f} GB")
