from image_to_desc import ImageToDesc
import json
from progress.bar import Bar
import time
from copy import deepcopy

IMAGE_DATA_PATH = 'C:\\Users\\vzhang\\workplace\\GenItenerary\\data\\scraped_data_remain2.json'
POI_DATA_PATH = 'C:\\Users\\vzhang\\workplace\\GenItenerary\\data\\itineraries.json'

dict_template = {
    "messages": [
        {
            "role": "system",
            "content": "You are a travel assistant that creates blogs based on image descriptions and POI names."
        },
        {
            "role": "user",
            "content": """
            Given a chronological sequence of image descriptions and POIs with descriptions, generate a travel blog. Keep the tone conversational and informative—like a real traveler sharing experiences rather than a scripted story.
            """
        },
        {
            "role": "user",
            "content": {
                "images": [],
                "pois": []
            }
        },
        {
            "role": "assistant",
            "content": None
        }
    ]
}

# Load JSON data
with open(IMAGE_DATA_PATH, "r", encoding="utf-8") as file:
    image_data = json.load(file)
print("Loaded Raw Image Data.")

with open(POI_DATA_PATH, "r", encoding="utf-8") as file:
    poi_data = json.load(file)
print("Loaded Raw POI Data.")

# Filter entries
image_data = [
    entry for entry in image_data
    if "error" not in entry and len(entry.get("images", {})) > 3
]
print("Entries Filtered.")

# Create a lookup dictionary for POI data by URL
poi_lookup = {entry["url"]: entry for entry in poi_data}

def process_images(images):
    results = []
    for img in images.values():
        try:
            if ImageToDesc.is_base64(img):
                thing = ImageToDesc(img).desc
                if thing != "Limit Exceeded":
                  results.append({"description": thing})
                  time.sleep(1)  # Wait for 1 second before processing the next image
                else:
                    results.append(None)
                    print("Limit Exceeded.")
                    return results
            else:
                print("Skipping invalid image format.")
        except Exception as e:
            print(f"Error processing image: {e}. Continuing to next image.")
            continue  # Continue processing next image
    return results

def extract_pois(pois_data):
    pois_list = []
    for day, places in pois_data.get("pois", {}).get("pois", {}).items():
        for name, details in places.items():
            pois_list.append({"name": name, "description": details["desc"]})
    return pois_list

# Combine data
combined_data = []
with Bar('Extracting Image Data', max=len(image_data)) as bar:
    for entry in image_data:
        try:
            url = entry["url"]
            print(" Now reading", entry["url"])
            if url in poi_lookup:
                poi_entry = poi_lookup[url]  # Get matching entry from second dataset
                
                combined_entry = deepcopy(dict_template)
                combined_entry["messages"][2]["content"]["images"] = process_images(entry["images"])
                combined_entry["messages"][2]["content"]["pois"] = extract_pois(poi_entry)
                combined_entry["messages"][3]["content"] = entry.get("text_content", "")
                
                combined_data.append(combined_entry)
                if None in combined_entry["messages"][2]["content"]["images"]:
                    combined_entry["messages"][2]["content"]["images"].remove(None)
                    break
                time.sleep(1)
                bar.next()
        except Exception as e:
            print(f"Error processing entry: {e}. Continuing to next entry.")
            continue  # Continue processing next entry

# Save processed data
with open("fine_tune_data3.jsonl", "w", encoding="utf-8") as f:
    for item in combined_data:
        json.dump(item, f)
        f.write('\n')

print(f"Processed {len(combined_data)} entries successfully.")
