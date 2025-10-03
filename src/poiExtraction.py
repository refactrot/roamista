from blog import Blog
import re, ast
import json
from poi import Poi
from opencage.geocoder import OpenCageGeocode
from itinerary import Itinerary
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENCAGE_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

class POIExtraction:
    def createPoi(geocoder, name, description, dur, day):
        name = name.replace(',', '')
        result = geocoder.geocode(name)
        if result:
            return Poi(name, result[0]['geometry']['lat'], result[0]['geometry']['lng'], description, dur, day)
        return Poi(name, None, None, description, dur, day)

    def extract_pois(blog: Blog):
        geolocator = OpenCageGeocode(api_key)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": '''Given an itinerary text, return ONLY a Python dictionary with the keys being the extracted names of ALL the poi stops and all locations visited and the values being a list of the realistic estimated duration in hours of each poi based on information in the text (minimum 0.25), the day number (if not mentioned default 0), and an extracted sentence description from text. The pois should be chronological and rounded to the nearest quarter hour, e.g. {"Louvre": [5.5, 1, "The Louvre is a museum with arts from the Renaissance"], "Arc de Triomphe": [.25, 2, "The Arc de Triomphe honors soldiers during the French revolution"]}.'''
                },
                {
                    "role": "user",
                    "content": blog.text,
                }
            ]
        )
        response = completion.choices[0].message

        raw_dict = POIExtraction.parse_string(response.content)
        lst = []
        for key, val in raw_dict.items():
            lst.append(POIExtraction.createPoi(geolocator, key, val[2], val[0], val[1]))
        return lst

    def parse_string(string):
        match = re.search(r'\{.*?\}', string, re.DOTALL)
        if match:
            dict_str = match.group()
            try:
                result_dict = ast.literal_eval(dict_str)
                return result_dict
            except Exception as e:
                print("Error parsing dictionary:", e)
                return {}
    
    def first_10_words(text):
        words = text.split()
        return ' '.join(words[:10])

    def write_json():
        with open("data/scraped_data_2.json", "r", encoding="utf-8", errors="replace") as file:
            try:
                data = json.load(file)
                print("File loaded.")
            except Exception as e:
                print(e)
                data = None

        data = [entry for entry in data if "error" not in entry]
        final = []  # Store all entries

        for blog in data:
            print("Parsing next blog...")
            blog = Blog.load_blog(blog)
            pois = POIExtraction.extract_pois(blog)
            itin = Itinerary(pois)
            entry = {
                "city": blog.city,
                "url": blog.url,
                "title": POIExtraction.first_10_words(blog.text),
                "length": itin.length,
                "pois": itin.group_pois_by_day(),
                #"images": blog.images,
            }
            final.append(entry)  # Append to the list

        # Write entire list to JSON
        output_file = "data/itineraries_2.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final, f, indent=4, ensure_ascii=False)

        print("File ready.")

POIExtraction.write_json()

