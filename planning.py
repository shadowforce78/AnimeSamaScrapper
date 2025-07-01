import requests
import re
import json

def url_maker(url):
    path = "https://cdn.statically.io/gh/Anime-Sama/IMG/img/contenu/"
    return f"{path}{url}.jpg"

def scrape_planning():
    """
    Fonction pour scraper le planning d'Anime-Sama
    
    Returns:
        list: Liste des scans avec leurs jours de sortie
    """
    url = "https://anime-sama.fr/planning/"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Erreur lors de la récupération de la page: {response.status_code}")
        return []
    
    content = response.text
    
    # Pattern to match cartePlanningScan calls (excluding commented lines)
    pattern = r'^\s*cartePlanningScan\("([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)",\s*"([^"]*)"\);'
    
    planning_data = []
    
    # Find all day sections using the titreJours class
    day_pattern = r'<h2 class="titreJours[^"]*"[^>]*>\s*([^<]+)\s*</h2>'
    day_matches = list(re.finditer(day_pattern, content, re.IGNORECASE))
    
    for i, day_match in enumerate(day_matches):
        day_name = day_match.group(1).strip()
        
        # Find the start and end of this day's section
        section_start = day_match.end()
        
        # Find the next day section or end of content
        if i + 1 < len(day_matches):
            section_end = day_matches[i + 1].start()
        else:
            # For the last day (usually Sunday), we need to be more careful
            # Look for a script tag that might contain permanent scans
            # Find the end of the current day's script section
            script_end_pattern = r'</script>\s*</div>\s*</div>'
            script_end_match = re.search(script_end_pattern, content[section_start:])
            if script_end_match:
                section_end = section_start + script_end_match.end()
            else:
                section_end = len(content)
        
        # Extract content for this day
        day_content = content[section_start:section_end]
        
        # Find all cartePlanningScan in this day's section (excluding commented ones)
        day_scan_matches = re.findall(pattern, day_content, re.MULTILINE)
        
        for match in day_scan_matches:
            name, url, image, time, status, lang = match
            # Skip template entries with variables and commented entries
            if name not in ["nom", ""] and not name.startswith("${"):
                planning_data.append({
                    "day": day_name,
                    "name": name,
                    "url": url,
                    "image": url_maker(image),
                    "time": time,
                    "status": status,
                    "language": lang
                })
    
    # Look for scans that are outside the day sections (permanent scans)
    # Find content after all day sections
    if day_matches:
        # Find the end of the last day section properly
        last_day_match = day_matches[-1]
        last_day_start = last_day_match.end()
        
        # Look for the end of the last day's script section
        script_end_pattern = r'</script>\s*</div>\s*</div>'
        script_end_match = re.search(script_end_pattern, content[last_day_start:])
        
        if script_end_match:
            last_day_real_end = last_day_start + script_end_match.end()
            remaining_content = content[last_day_real_end:]
            
            # Look for permanent scans in the remaining content (excluding commented ones)
            permanent_matches = re.findall(pattern, remaining_content, re.MULTILINE)
            
            for match in permanent_matches:
                name, url, image, time, status, lang = match
                # Skip template entries and check for duplicates
                if name not in ["nom", ""] and not name.startswith("${"):
                    # Check if this scan is already in our data
                    existing = any(item["name"] == name and item["url"] == url for item in planning_data)
                    if not existing:
                        planning_data.append({
                            "day": "Autres",
                            "name": name,
                            "url": url, 
                            "image": url_maker(image),
                            "time": time,
                            "status": status,
                            "language": lang
                        })
    
    return planning_data

if __name__ == "__main__":
    # Script principal - ne s'exécute que si le fichier est appelé directement
    planning_data = scrape_planning()
    
    # Save as JSON
    with open("planning_data.json", "w", encoding="utf-8") as file:
        json.dump(planning_data, file, ensure_ascii=False, indent=2)
    
    print(f"Extraction terminée ! {len(planning_data)} entrées cartePlanningScan trouvées.")
    
    # Print summary by day
    day_counts = {}
    for item in planning_data:
        day = item["day"]
        day_counts[day] = day_counts.get(day, 0) + 1
    
    print("\nRépartition par jour:")
    for day, count in day_counts.items():
        print(f"  {day}: {count} scans")