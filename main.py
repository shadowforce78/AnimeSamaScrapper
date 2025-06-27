import requests
import bs4 as bs
import json
import os
import re
from urllib.parse import urljoin

url = "https://anime-sama.fr"
catalog = "/catalogue"
page_param = "?page="  # Renamed to avoid conflict with page content


def get_anime_list():
    all_anime_content = []
    current_page = 1
    while True:
        response = requests.get(url + catalog + page_param + str(current_page))
        if response.status_code == 200:
            soup = bs.BeautifulSoup(response.content, "html.parser")
            anime_list_div = soup.find("div", id="list_catalog")

            if anime_list_div:
                div_content = str(anime_list_div)
                if (
                    "Aucun résultat trouvé, vérifiez bien votre recherche."
                    in div_content
                ):
                    break  # Stop if the phrase is found
                all_anime_content.append(div_content)
                current_page += 1
            else:
                # If the div is not found, it might be an error or end of pages
                print(f"Div 'list_catalog' not found on page {current_page}")
                break
        else:
            print(f"Failed to retrieve page {current_page}")
            break

    if not all_anime_content:
        return None
    return "\\\\n".join(all_anime_content)


def refine_data(html_file_path):
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = bs.BeautifulSoup(html_content, "html.parser")
    anime_items = []

    for anime_div in soup.find_all(
        "div",
        class_="shrink-0 m-3 rounded border-2 border-gray-400 border-opacity-50 shadow-2xl shadow-black hover:shadow-zinc-900 hover:opacity-80 bg-black bg-opacity-40 transition-all duration-200 cursor-pointer",
    ):
        data = {}
        link_tag = anime_div.find("a", class_="flex divide-x")
        if link_tag:
            data["url"] = link_tag.get("href")

        img_tag = anime_div.find("img")
        if img_tag:
            data["image_url"] = img_tag.get("src")

        info_div = anime_div.find(
            "div", class_="infoCarteHorizontale bg-black bg-opacity-40 p-2 pl-3"
        )
        if info_div:
            title_tag = info_div.find(
                "h1", class_="text-white font-bold uppercase text-md line-clamp-2"
            )
            if title_tag:
                data["title"] = title_tag.get_text(strip=True)

            paragraphs = info_div.find_all(
                "p", class_="text-white text-xs opacity-40 truncate italic"
            )
            if len(paragraphs) > 0 and paragraphs[0]:
                data["alt_title"] = paragraphs[0].get_text(strip=True)

            genre_tags = info_div.find_all(
                "p", class_="mt-0.5 text-gray-300 font-medium text-xs truncate"
            )

            if len(genre_tags) > 0 and genre_tags[0]:
                data["genres"] = [
                    genre.strip()
                    for genre in genre_tags[0].get_text(strip=True).split(",")
                ]
            if len(genre_tags) > 1 and genre_tags[1]:
                data["type"] = genre_tags[1].get_text(strip=True)
            if len(genre_tags) > 2 and genre_tags[2]:
                data["language"] = genre_tags[2].get_text(strip=True)

        if data:  # Add data only if some information was extracted
            # Conserver tous les items qui contiennent "Scans" ou "Manhwa" dans leur type
            if "type" in data and (
                "Scans" in data["type"]
                or "Manhwa" in data["type"]
                or "manhwa" in data["type"].lower()
            ):
                anime_items.append(data)
                print(
                    f"Item trouvé avec type '{data['type']}': {data.get('title', 'Sans titre')}"
                )

    print(f"Total des items 'Scans' ou 'Manhwa' trouvés: {len(anime_items)}")
    return json.dumps(anime_items, indent=4, ensure_ascii=False)


def fetch_scan_page_urls(anime_data_list):  # Function name kept for menu consistency
    """
    Fetches scan types (e.g., Scan VF, Scan Spécial VF) and their URLs
    for items of type 'Scans' from their main catalog page using regex.
    anime_data_list: A list of dictionaries, where each dictionary is an anime/manga item.
    Returns a new list with 'scan_types' added to relevant items.
    """
    updated_anime_data_list = []
    if not isinstance(anime_data_list, list):
        print("Error: fetch_scan_page_urls expects a list of dictionaries.")
        return anime_data_list

    # Multiple regex patterns to try, in order
    scan_patterns = [
        r'panneauScan\("([^"]+)",\s*"([^"]+)"\);',  # Standard pattern (without double escapes)
        r'panneauScan\\\\?"([^"]+)",\\\\?s*"([^"]+)"\\\\?\\);',  # More flexible pattern
        r'panneauScan\([\'"](.*?)[\'"]\s*,\s*[\'"](.*?)[\'"]',  # Even more flexible
    ]

    for anime_item in anime_data_list:
        current_item_copy = anime_item.copy()
        # Look for "Scans" in type (either exact match or contained in string)
        if (
            current_item_copy.get("type") == "Scans"
            or ("type" in current_item_copy and "Scans" in current_item_copy["type"])
            or (
                "type" in current_item_copy
                and "scans" in current_item_copy["type"].lower()
            )
        ) and current_item_copy.get("url"):

            item_main_page_url = current_item_copy["url"]
            # Ensure the base URL for urljoin ends with a slash if it's a directory-like URL
            if not item_main_page_url.endswith("/"):
                item_main_page_url_for_join = item_main_page_url + "/"
            else:
                item_main_page_url_for_join = item_main_page_url

            item_title = current_item_copy.get("title", item_main_page_url)
            print(
                f"Processing for scan types: {item_title} (from {item_main_page_url})"
            )

            try:
                response = requests.get(item_main_page_url, timeout=10)
                response.raise_for_status()
                html_content = response.text  # Get HTML content for regex

                # Print a snippet of the HTML for debugging
                content_snippet = html_content[: min(500, len(html_content))]
                # print(f"  HTML snippet (first 500 chars): {content_snippet}")

                # Check for an indication that panneauScan function exists in the HTML
                if "panneauScan" in html_content:
                    print("  Found 'panneauScan' function reference in HTML")
                else:
                    print("  No 'panneauScan' function reference found in HTML")

                found_scan_types = []

                # Try different regex patterns
                for pattern in scan_patterns:
                    scan_matches = re.findall(pattern, html_content)
                    if scan_matches:
                        print(f"  Found matches with pattern: {pattern}")
                        break
                # Process regex matches if any were found
                for name, relative_url_path in scan_matches:
                    absolute_url = urljoin(
                        item_main_page_url_for_join, relative_url_path.strip()
                    )
                    found_scan_types.append({"name": name.strip(), "url": absolute_url})
                    print(f"  Found scan type: {name.strip()} - {absolute_url}")

                # Remove the first entry as it's always "name = nom" and "url = url"
                if len(found_scan_types) > 0:
                    print(f"  Removing first entry: {found_scan_types[0]}")
                    found_scan_types.pop(0)
                    print(f"  Remaining scan types: {len(found_scan_types)}")

                # Fallback: If no matches were found, try constructing common scan URLs
                if not found_scan_types:
                    print(
                        "  No scan types found via regex. Trying fallback URL construction..."
                    )
                    # Common scan URL patterns
                    potential_paths = ["/scan/vf/", "/scan_special/vf/"]
                    for path in potential_paths:
                        potential_url = urljoin(item_main_page_url_for_join, path)

                        # Make a HEAD request to check if the URL exists
                        try:
                            head_response = requests.head(potential_url, timeout=5)
                            if head_response.status_code == 200:
                                if path == "/scan/vf/":
                                    name = "Scan VF"
                                else:
                                    name = "Scan Spécial VF"
                                found_scan_types.append(
                                    {"name": name, "url": potential_url}
                                )
                                print(
                                    f"  Fallback found scan type: {name} - {potential_url}"
                                )
                        except Exception as e:
                            print(
                                f"  Error checking potential URL {potential_url}: {e}"
                            )

                if found_scan_types:
                    current_item_copy["scan_types"] = (
                        found_scan_types  # Changed key to scan_types
                    )
                else:
                    print(f"  No scan types found for {item_title}.")

            except requests.exceptions.Timeout:
                print(
                    f"  Timeout while fetching page {item_main_page_url} for scan types."
                )
            except requests.exceptions.RequestException as e:
                print(f"  Error fetching page {item_main_page_url} for scan types: {e}")
            except Exception as e:
                print(
                    f"  An unexpected error occurred while processing {item_title} for scan types: {e}"
                )

        updated_anime_data_list.append(current_item_copy)

    return updated_anime_data_list


def get_scan_chapters(anime_data_list):
    """
    Pour chaque entrée avec 'scan_types', récupère les chapitres disponibles
    en utilisant les méthodes de l'API (trouver l'ID du scan, puis analyser episodes.js)
    """
    updated_anime_data_list = []
    if not isinstance(anime_data_list, list):
        print("Error: get_scan_chapters expects a list of dictionaries.")
        return anime_data_list

    # User agent header pour éviter les blocages
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for anime_item in anime_data_list:
        current_item_copy = anime_item.copy()

        # Vérifier si l'élément a des 'scan_types'
        if current_item_copy.get("scan_types") and isinstance(
            current_item_copy["scan_types"], list
        ):
            scan_chapters_data = []

            for scan_type in current_item_copy["scan_types"]:
                scan_url = scan_type.get("url", "")
                scan_name = scan_type.get("name", "Scan")

                if not scan_url:
                    continue

                print(f"Processing chapters for: {scan_name} at {scan_url}")

                try:
                    # Faire la requête pour trouver l'ID du scan
                    response = requests.get(scan_url, headers=headers, timeout=15)

                    if response.status_code != 200:
                        print(
                            f"  Failed to access page, status code: {response.status_code}"
                        )
                        continue

                    # Analyser la réponse pour trouver l'ID du scan
                    soup = bs.BeautifulSoup(response.text, "html.parser")
                    html_content = response.text

                    # Essayer plusieurs méthodes pour trouver l'ID du scan
                    id_scan = None

                    # Method 1: Look for script tags with episodes.js?filever=
                    script_tags = soup.find_all("script")
                    for script in script_tags:
                        if script.get("src") and "episodes.js?filever=" in script.get(
                            "src"
                        ):
                            match = re.search(r"filever=(\d+)", script.get("src"))
                            if match:
                                id_scan = match.group(1)
                                print(f"  Scan ID found (method 1): {id_scan}")
                                break

                    # Method 2: Look for script tags containing episodes.js?filever= in their text content
                    if not id_scan:
                        for script in script_tags:
                            if (
                                script.string
                                and "episodes.js?filever=" in script.string
                            ):
                                match = re.search(r"filever=(\d+)", script.string)
                                if match:
                                    id_scan = match.group(1)
                                    print(f"  Scan ID found (method 2): {id_scan}")
                                    break

                    # Method 3: Check for inline scripts that might define the scan ID
                    if not id_scan:
                        for script in script_tags:
                            if script.string:
                                match = re.search(
                                    r'(?:scanID|idScan|id_scan|filever)\s*=\s*[\'"]?(\d+)[\'"]?',
                                    script.string,
                                )
                                if match:
                                    id_scan = match.group(1)
                                    print(f"  Scan ID found (method 3): {id_scan}")
                                    break

                    # Method 4: Look for script tags with src attribute containing a version number
                    if not id_scan:
                        for script in script_tags:
                            src = script.get("src")
                            if src and re.search(r"\.js\?v=(\d+)", src):
                                match = re.search(r"\.js\?v=(\d+)", src)
                                if match:
                                    id_scan = match.group(1)
                                    print(f"  Scan ID found (method 4): {id_scan}")
                                    break

                    # Method 5: Look for any HTML element with data-id attribute
                    if not id_scan:
                        elements_with_data_id = soup.find_all(
                            attrs={"data-id": re.compile(r"\d+")}
                        )
                        if elements_with_data_id:
                            id_scan = elements_with_data_id[0].get("data-id")
                            print(f"  Scan ID found (method 5): {id_scan}")

                    # If all else fails, extract the raw HTML and search for common patterns
                    if not id_scan:
                        patterns = [
                            r"episodes\.js\?filever=(\d+)",
                            r"episodes\.js\?v=(\d+)",
                            r'scan_id\s*=\s*[\'"]?(\d+)[\'"]?',
                            r'id_scan\s*=\s*[\'"]?(\d+)[\'"]?',
                            r'scanID\s*=\s*[\'"]?(\d+)[\'"]?',
                            r'data-id=[\'"](\d+)[\'"]',
                            r"scan/(\d+)/",
                        ]

                        for pattern in patterns:
                            match = re.search(pattern, html_content)
                            if match:
                                id_scan = match.group(1)
                                print(f"  Scan ID found (general pattern): {id_scan}")
                                break

                    # Si aucun ID n'a été trouvé, passer au scan suivant
                    if not id_scan:
                        print(f"  No scan ID found for {scan_url}")
                        continue

                    # Construire l'URL du fichier episodes.js
                    # Extraire le nom et le chemin de l'URL du scan
                    scan_url_parts = scan_url.rstrip("/").split("/catalogue/")
                    if len(scan_url_parts) != 2:
                        print(f"  Invalid scan URL format: {scan_url}")
                        continue

                    scan_path = scan_url_parts[1]
                    episodes_url = (
                        f"{url}/catalogue/{scan_path}/episodes.js?filever={id_scan}"
                    )

                    print(f"  Fetching episodes from: {episodes_url}")

                    # Faire la requête pour récupérer le script episodes.js
                    episodes_response = requests.get(
                        episodes_url, headers=headers, timeout=15
                    )

                    if episodes_response.status_code != 200:
                        print(
                            f"  Failed to access episodes.js, status code: {episodes_response.status_code}"
                        )
                        continue

                    # Récupérer le contenu brut
                    raw_content = (
                        episodes_response.text
                    )  # Analyser le contenu JavaScript pour extraire les données des chapitres
                    chapters_result = parse_episodes_js(raw_content)

                    if chapters_result and chapters_result.get("chapters"):
                        chapters_data = chapters_result["chapters"]
                        total_chapters = chapters_result["total_chapters"]

                        # Ajouter les informations récupérées
                        scan_chapters_info = {
                            "name": scan_name,
                            "url": scan_url,
                            "id_scan": id_scan,
                            "episodes_url": episodes_url,
                            "total_chapters": total_chapters,
                            "chapters": chapters_data,
                        }
                        scan_chapters_data.append(scan_chapters_info)
                        print(f"  Added {total_chapters} chapters for {scan_name}")

                        # Afficher un résumé des pages par chapitre
                        total_pages = sum(
                            chapter.get("page_count", 0) for chapter in chapters_data
                        )
                        if total_pages > 0:
                            print(f"  Total pages across all chapters: {total_pages}")
                    else:
                        print(f"  No chapters found in episodes.js for {scan_name}")

                except requests.exceptions.Timeout:
                    print(f"  Timeout while retrieving data for {scan_name}")
                except requests.exceptions.RequestException as e:
                    print(f"  Request error while retrieving data for {scan_name}: {e}")
                except Exception as e:
                    print(
                        f"  An unexpected error occurred while processing {scan_name}: {e}"
                    )  # Si nous avons trouvé des données de chapitres, les ajouter à l'élément
            if scan_chapters_data:
                current_item_copy["scan_chapters"] = scan_chapters_data

        updated_anime_data_list.append(current_item_copy)

    return updated_anime_data_list


def convert_google_drive_url(url):
    """
    Convertit une URL Google Drive de visualisation vers une URL de téléchargement direct.

    Args:
        url (str): URL Google Drive de visualisation

    Returns:
        str: URL de téléchargement direct ou URL originale si conversion impossible
    """
    try:
        # Vérifier si c'est un lien Google Drive
        if "drive.google.com" not in url:
            return url

        # Pattern pour extraire l'ID du fichier Google Drive
        patterns = [
            r"drive\.google\.com/uc\?export=view&id=([a-zA-Z0-9_-]+)",  # Format uc?export=view&id=
            r"drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",  # Format file/d/ID
            r"id=([a-zA-Z0-9_-]+)",  # Recherche générale d'ID
        ]

        file_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                file_id = match.group(1)
                break

        # Si aucun ID trouvé, retourner l'URL originale
        if not file_id:
            return url

        # Construire l'URL de téléchargement direct
        download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=view&authuser=0"
        return download_url

    except Exception as e:
        print(f"  Erreur lors de la conversion de l'URL Google Drive: {e}")
        return url


def parse_episodes_js(raw_content):
    """
    Analyser le contenu JavaScript du fichier episodes.js pour extraire les données des chapitres.
    Le format peut être:
    1. var eps[numero] = [array_of_image_urls]; (format classique)
    2. var eps[numero] = []; eps[numero].length = X; (format avec longueur séparée)

    Returns:
        dict: {
            'total_chapters': int,
            'chapters': list of dict with chapter info including page_count
        }
    """
    chapters = []

    try:
        # Pattern 1: var eps[numero] = [tableau d'URLs]; (format classique)
        chapter_pattern = r"var eps(\d+)=\s*\[(.*?)\];"
        chapter_matches = re.findall(chapter_pattern, raw_content, re.DOTALL)

        print(f"  Found {len(chapter_matches)} chapter definitions")

        # Pattern 2: eps[numero].length = X; (format avec longueur séparée)
        length_pattern = r"eps(\d+)\.length\s*=\s*(\d+);"
        length_matches = re.findall(length_pattern, raw_content)
        
        print(f"  Found {len(length_matches)} length definitions")

        # Créer un dictionnaire pour stocker les longueurs définies séparément
        chapter_lengths = {}
        for chapter_num, length in length_matches:
            chapter_lengths[chapter_num] = int(length)
            print(f"    Length definition: eps{chapter_num}.length = {length}")

        for chapter_num, urls_content in chapter_matches:
            page_count = 0
            
            # Vérifier si le contenu du tableau est vide ou contient peu de données
            urls_content_clean = urls_content.strip()
            
            if not urls_content_clean or len(urls_content_clean) < 10:
                # Tableau vide ou presque, vérifier s'il y a une définition de longueur
                if chapter_num in chapter_lengths:
                    page_count = chapter_lengths[chapter_num]
                    print(f"    Chapitre {chapter_num}: {page_count} pages (via length property)")
                else:
                    print(f"    Chapitre {chapter_num}: tableau vide, pas de longueur définie")
                    continue
            else:
                # Format classique : compter les URLs dans le contenu du tableau
                url_pattern = r"'([^']+)'"
                image_urls = re.findall(url_pattern, urls_content)
                
                # Compter seulement les URLs non vides
                page_count = len([url for url in image_urls if url.strip()])
                print(f"    Chapitre {chapter_num}: {page_count} pages trouvées (via comptage URLs)")

            if page_count > 0:  # Ne garder que les chapitres avec des pages
                chapter_data = {
                    "number": chapter_num,
                    "title": f"Chapitre {chapter_num}",
                    "page_count": page_count,
                }
                
                chapters.append(chapter_data)

        # Trier les chapitres par numéro
        def chapter_sort_key(chapter):
            try:
                return int(chapter["number"])
            except ValueError:
                return float("inf")

        chapters.sort(key=chapter_sort_key)

        print(f"  Total chapters processed: {len(chapters)}")

        # Retourner un dictionnaire avec le nombre total de chapitres et la liste des chapitres
        return {"total_chapters": len(chapters), "chapters": chapters}

    except Exception as e:
        print(f"  Error parsing episodes.js file: {e}")
        # Sauvegarder le contenu brut pour déboguer en cas d'erreur
        debug_filename = f"debug_episodes_{len(raw_content)}.js"
        try:
            with open(debug_filename, "w", encoding="utf-8") as f:
                f.write(raw_content)
            print(f"  Debug file saved as: {debug_filename}")
        except:
            pass

    # Retourner une structure vide en cas d'erreur
    return {"total_chapters": 0, "chapters": []}


def process_all_steps_in_order():
    """
    Exécute toutes les étapes de scraping dans l'ordre :
    1. Scrape new anime catalog data
    2. Load catalog data from JSON
    3. Fetch scan types for loaded 'Scans' type entries
    4. Fetch chapters data for items with scan types

    Returns:
        bool: True si toutes les étapes se sont bien déroulées, False sinon
    """
    anime_list_html_file = "anime_list.html"
    anime_data_json_file = "anime_data.json"
    current_data_object = None

    try:
        # Étape 1: Scrape new anime catalog data
        print("Étape 1/4: Scraping du catalogue d'anime...")
        anime_list_html = get_anime_list()
        if not anime_list_html:
            print("Erreur: Impossible de récupérer la liste HTML des animes")
            return False

        print("Liste HTML des animes récupérée avec succès.")
        with open(anime_list_html_file, "w", encoding="utf-8") as file:
            file.write(anime_list_html)

        # Étape 2: Raffiner les données
        print("Étape 2/4: Raffinage des données...")
        refined_anime_data_json_string = refine_data(anime_list_html_file)
        if not refined_anime_data_json_string:
            print("Erreur: Aucune donnée raffinée")
            return False

        try:
            current_data_object = json.loads(refined_anime_data_json_string)
            print(
                f"Données raffinées avec succès: {len(current_data_object)} éléments."
            )
            with open(anime_data_json_file, "w", encoding="utf-8") as json_file_out:
                json.dump(
                    current_data_object, json_file_out, indent=4, ensure_ascii=False
                )
            print(f"Données JSON sauvegardées dans {anime_data_json_file}")
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON: {e}")
            return False

        # Étape 3: Fetch scan types
        print("Étape 3/4: Récupération des types de scan...")
        if isinstance(current_data_object, list):
            current_data_object = fetch_scan_page_urls(current_data_object)
            print("Processus de récupération des types de scan terminé.")
            with open(
                anime_data_json_file, "w", encoding="utf-8"
            ) as json_file_out_scans:
                json.dump(
                    current_data_object,
                    json_file_out_scans,
                    indent=4,
                    ensure_ascii=False,
                )
            print(
                f"Données mises à jour avec les types de scan sauvegardées dans {anime_data_json_file}"
            )
        else:
            print("Erreur: Données non dans le format de liste attendu")
            return False

        # Étape 4: Fetch chapters data
        print("Étape 4/4: Récupération des données de chapitres...")
        if any(
            item.get("scan_types")
            for item in current_data_object
            if isinstance(item, dict)
        ):
            current_data_object = get_scan_chapters(current_data_object)
            print("Processus de récupération des données de chapitres terminé.")
            with open(
                anime_data_json_file, "w", encoding="utf-8"
            ) as json_file_out_chapters:
                json.dump(
                    current_data_object,
                    json_file_out_chapters,
                    indent=4,
                    ensure_ascii=False,
                )
            print(
                f"Données mises à jour avec les chapitres sauvegardées dans {anime_data_json_file}"
            )
        else:
            print("Aucun élément avec des types de scan trouvé")
            return False

        print("✅ Toutes les étapes ont été exécutées avec succès !")
        return True

    except Exception as e:
        print(f"Erreur lors de l'exécution des étapes: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    anime_list_html_file = "anime_list.html"
    anime_data_json_file = "anime_data.json"
    current_data_object = None  # To hold the data (list of dicts) in memory

    while True:
        print("\\\\nMenu:")
        print("1. Scrape new anime catalog data")
        if os.path.exists(anime_data_json_file):
            print(f"2. Load catalog data from {anime_data_json_file}")
        if current_data_object:
            # Updated menu option text to reflect scan types
            print("3. Fetch scan types for loaded 'Scans' type entries")
            if any(
                item.get("scan_types")
                for item in current_data_object
                if isinstance(item, dict)
            ):
                print("4. Fetch chapters data for items with scan types")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            print("Scraping new data...")
            anime_list_html = get_anime_list()
            if anime_list_html:
                print("Anime list HTML retrieved successfully.")
                with open(anime_list_html_file, "w", encoding="utf-8") as file:
                    file.write(anime_list_html)

                refined_anime_data_json_string = refine_data(anime_list_html_file)
                if refined_anime_data_json_string:
                    try:
                        current_data_object = json.loads(refined_anime_data_json_string)
                        print("\\\\nRefined Anime Data (JSON):")
                        print(
                            f"Successfully refined {len(current_data_object) if isinstance(current_data_object, list) else 'N/A'} items."
                        )
                        with open(
                            anime_data_json_file, "w", encoding="utf-8"
                        ) as json_file_out:
                            json.dump(
                                current_data_object,
                                json_file_out,
                                indent=4,
                                ensure_ascii=False,
                            )
                        print(f"\\\\nJSON data saved to {anime_data_json_file}")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding refined JSON string: {e}")
                        current_data_object = None
                else:
                    print("No data was refined.")
                    current_data_object = None
            else:
                print("Failed to retrieve anime list HTML.")
                current_data_object = None

        elif choice == "2" and os.path.exists(anime_data_json_file):
            print(f"Loading data from {anime_data_json_file}...")
            try:
                with open(anime_data_json_file, "r", encoding="utf-8") as json_file_in:
                    current_data_object = json.load(json_file_in)
                print("\\\\nExisting Anime Data (JSON) loaded:")
                print(
                    f"Successfully loaded {len(current_data_object) if isinstance(current_data_object, list) else 'N/A'} items."
                )
            except json.JSONDecodeError:
                print(
                    f"Error: Could not decode JSON from {anime_data_json_file}. The file might be corrupted."
                )
                current_data_object = None
            except Exception as e:
                print(f"An error occurred while reading {anime_data_json_file}: {e}")
                current_data_object = None

        elif choice == "3" and current_data_object:
            print("Fetching scan types...")  # Updated print
            if isinstance(current_data_object, list):
                current_data_object = fetch_scan_page_urls(current_data_object)
                print("Scan type fetching process complete.")  # Updated print
                with open(
                    anime_data_json_file, "w", encoding="utf-8"
                ) as json_file_out_scans:
                    json.dump(
                        current_data_object,
                        json_file_out_scans,
                        indent=4,
                        ensure_ascii=False,
                    )
                # Updated print message to reflect scan types
                print(f"Updated data with scan types saved to {anime_data_json_file}")
            else:
                print(
                    "No data loaded or data is not in the expected list format. Please load or scrape data first."
                )

        elif (
            choice == "4"
            and current_data_object
            and any(
                item.get("scan_types")
                for item in current_data_object
                if isinstance(item, dict)
            )
        ):
            print("Fetching scan chapters data...")
            if isinstance(current_data_object, list):
                current_data_object = get_scan_chapters(current_data_object)
                print("Scan chapters data fetching process complete.")
                with open(
                    anime_data_json_file, "w", encoding="utf-8"
                ) as json_file_out_chapters:
                    json.dump(
                        current_data_object,
                        json_file_out_chapters,
                        indent=4,
                        ensure_ascii=False,
                    )
                print(
                    f"Updated data with scan chapters saved to {anime_data_json_file}"
                )
            else:
                print("No data loaded or data is not in the expected list format.")
        elif choice == "5":
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")
