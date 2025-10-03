import requests
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import base64
import json
import time
import random
from urllib.parse import urljoin
from dotenv import load_dotenv, dotenv_values
import os

load_dotenv()
config = dotenv_values(".env")
api_key = os.getenv("SERP_API_KEY")

# Define cities to search for travel blogs
cities = [
    "New York", "London", "Paris", "Tokyo", "Dubai", "Singapore", "Hong Kong", "Los Angeles", 
    "Shanghai", "Beijing", "San Francisco", "Toronto", "Sydney", "Berlin", "Chicago", "Seoul", 
    "Amsterdam", "Barcelona", "Madrid", "Moscow", "Bangkok", "Rome", "Istanbul", "Vienna", 
    "São Paulo", "Mumbai", "Mexico City", "Zurich", "Boston", "Melbourne", "Frankfurt", 
    "Jakarta", "Kuala Lumpur", "Stockholm", "Copenhagen", "Dublin", "Geneva", "Osaka", 
    "Buenos Aires", "Brussels", "Vancouver", "Hamburg", "Lisbon", "Warsaw", "Shenzhen", 
    "Rio de Janeiro", "Taipei", "Washington D.C.", "Johannesburg", "Munich", "Helsinki", 
    "Manila", "Doha", "Tel Aviv", "Milan", "Ho Chi Minh City", "Bogotá", "Lima", "Athens", 
    "Chengdu", "San Diego", "Bangalore", "Cairo", "Riyadh", "Prague", "Mexico City", 
    "Oslo", "Bucharest", "Budapest", "Brisbane", "Montreal", "Auckland", "Edinburgh", 
    "Denver", "Houston", "Santiago", "Abu Dhabi", "Taipei", "Cologne", "Kiev", "Hanoi", 
    "Marseille", "Lyon", "Perth", "Porto", "Guangzhou", "Chennai", "Stuttgart", "Riyadh", 
    "Nagoya", "Valencia", "Rotterdam", "Tel Aviv", "Birmingham", "Nagoya", "Havana", 
    "Luxembourg", "Seville", "Leeds", "Antwerp", "Gothenburg", "Florence", "Nairobi", 
    "Islamabad", "Kuwait City", "Kolkata", "Medellín"
]

search_results = []

# Dictionary to map URLs to their respective cities
url_city_map = {}

# Get URLs from Google search results using SerpAPI
for city in cities:
    params = {
        "q": f"{city} travel itinerary",
        "api_key": api_key,
        "num": 20  # Adjust for more results per city
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    if "organic_results" in results:
        for result in results["organic_results"]:
            url = result["link"]
            search_results.append(url)
            url_city_map[url] = city  # Keep track of which city the URL belongs to

# Function to fetch and encode images as Base64
def fetch_images(soup, base_url):
    images = {}
    img_tags = soup.find_all("img")

    for i, img in enumerate(img_tags):
        img_url = img.get("src")
        if img_url:
            img_url = urljoin(base_url, img_url)  # Convert to absolute URL

            try:
                img_response = requests.get(img_url, timeout=5)
                if img_response.status_code == 200:
                    img_data = base64.b64encode(img_response.content).decode("utf-8")
                    images[f"image_{i+1}"] = img_data
            except requests.exceptions.RequestException:
                continue  # Skip images that fail to load

    return images

def scrape_page(url, city):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise error for bad responses

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove unwanted sections (navigation bars, headers, footers)
        for tag in soup(["nav", "header", "footer", "aside"]):  
            tag.decompose()  # Remove these elements from the page
        
        text_content = soup.get_text(separator="\n", strip=True)  # Extract clean text
        images = fetch_images(soup, url)  # Extract images as Base64

        return {"url": url, "text_content": text_content, "images": images, "city": city}

    except requests.exceptions.RequestException as e:
        return {"url": url, "error": str(e), "city": city}

# Scrape and save data for all URLs
scraped_data = []

for url in search_results:
    city = url_city_map.get(url, "Unknown")  # Get the city corresponding to this URL
    print(f"Scraping {url} for city: {city}...\n")

    data = scrape_page(url, city)
    scraped_data.append(data)

    print(f"Scraped {len(data.get('images', {}))} images and saved content.\n" + "=" * 80)

    # Random delay to avoid getting blocked
    time.sleep(random.uniform(2, 5))

# Save to JSON file
output_file = "data/scraped_data.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(scraped_data, f, indent=4, ensure_ascii=False)

print(f"Scraping complete! Data saved to {output_file}")
