import requests
import bs4 as bs
import json
import os # Added import for os

url = "https://anime-sama.fr"
catalog = "/catalogue"
page_param = "?page="  # Renamed to avoid conflict with page content

def get_anime_list():
    all_anime_content = []
    current_page = 1
    while True:
        response = requests.get(url + catalog + page_param + str(current_page))
        if response.status_code == 200:
            soup = bs.BeautifulSoup(response.content, 'html.parser')
            anime_list_div = soup.find('div', id='list_catalog')

            if anime_list_div:
                div_content = str(anime_list_div)
                if "Aucun résultat trouvé, vérifiez bien votre recherche." in div_content:
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
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = bs.BeautifulSoup(html_content, 'html.parser')
    anime_items = []

    for anime_div in soup.find_all('div', class_="shrink-0 m-3 rounded border-2 border-gray-400 border-opacity-50 shadow-2xl shadow-black hover:shadow-zinc-900 hover:opacity-80 bg-black bg-opacity-40 transition-all duration-200 cursor-pointer"):
        data = {}
        link_tag = anime_div.find('a', class_="flex divide-x")
        if link_tag:
            data['url'] = link_tag.get('href')

        img_tag = anime_div.find('img')
        if img_tag:
            data['image_url'] = img_tag.get('src')

        info_div = anime_div.find('div', class_="infoCarteHorizontale bg-black bg-opacity-40 p-2 pl-3")
        if info_div:
            title_tag = info_div.find('h1', class_="text-white font-bold uppercase text-md line-clamp-2")
            if title_tag:
                data['title'] = title_tag.get_text(strip=True)

            paragraphs = info_div.find_all('p', class_="text-white text-xs opacity-40 truncate italic")
            if len(paragraphs) > 0 and paragraphs[0]:
                 data['alt_title'] = paragraphs[0].get_text(strip=True)


            genre_tags = info_div.find_all('p', class_="mt-0.5 text-gray-300 font-medium text-xs truncate")
            
            if len(genre_tags) > 0 and genre_tags[0]:
                data['genres'] = [genre.strip() for genre in genre_tags[0].get_text(strip=True).split(',')]
            if len(genre_tags) > 1 and genre_tags[1]:
                data['type'] = genre_tags[1].get_text(strip=True)
            if len(genre_tags) > 2 and genre_tags[2]:
                data['language'] = genre_tags[2].get_text(strip=True)
                
        if data: # Add data only if some information was extracted
            anime_items.append(data)
            
    return json.dumps(anime_items, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    anime_list_html_file = "anime_list.html"
    anime_data_json_file = "anime_data.json"

    while True:
        print("\\\\nMenu:")
        print("1. Scrape new anime data")
        if os.path.exists(anime_data_json_file):
            print(f"2. Use existing data from {anime_data_json_file}")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            print("Scraping new data...")
            anime_list_html = get_anime_list()
            if anime_list_html:
                print("Anime list retrieved successfully.")
                with open(anime_list_html_file, "w", encoding="utf-8") as file:
                    file.write(anime_list_html)
                
                refined_anime_data_json = refine_data(anime_list_html_file)
                if refined_anime_data_json:
                    print("\\\\nRefined Anime Data (JSON):")
                    print(refined_anime_data_json)
                    with open(anime_data_json_file, "w", encoding="utf-8") as json_file:
                        json_file.write(refined_anime_data_json)
                    print(f"\\\\nJSON data saved to {anime_data_json_file}")
                else:
                    print("No data to refine after scraping.")
            else:
                print("Failed to retrieve anime list.")
        elif choice == '2' and os.path.exists(anime_data_json_file):
            print(f"Loading data from {anime_data_json_file}...")
            try:
                with open(anime_data_json_file, "r", encoding="utf-8") as json_file:
                    existing_data = json.load(json_file) # Use json.load to parse the file content
                print("\\\\nExisting Anime Data (JSON):")
                print(json.dumps(existing_data, indent=4, ensure_ascii=False)) # Pretty print the loaded JSON
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from {anime_data_json_file}. The file might be corrupted.")
            except Exception as e:
                print(f"An error occurred while reading {anime_data_json_file}: {e}")
        elif choice == '3':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")