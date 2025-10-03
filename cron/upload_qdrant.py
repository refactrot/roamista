from sentence_transformers import SentenceTransformer
from dotenv import dotenv_values, load_dotenv
from qdrant_client import QdrantClient, models
from qdrant_client.models import VectorParams, Distance
import json

# Load environment variables
load_dotenv()
config = dotenv_values("./.env")

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=config["QDRANT_URL"],
    api_key=config["QDRANT_API_KEY"],
)

# Create/Recreate the collection
qdrant_client.recreate_collection(
   collection_name="itineraries_data",
   vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

# Load sentence transformer model for embedding
encoder = SentenceTransformer("all-MiniLM-L6-v2")

# Temporary document object to maintain consistency
class TempDocObject:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

# Function to process itinerary JSON file
def process_json(path):
    with open(path, encoding="utf8") as f:
        data = json.load(f)

    documents = []
    for itinerary in data:  # Assuming it's a list of itineraries
        description = f"{itinerary['title']} - {itinerary['city']}.\n"
        for poi_key, poi_details in itinerary.get("pois", {}).get("pois", {}).items():
            for name, details in poi_details.items():
                description += f"{name}: {details['desc']} (Duration: {details['dur']}h)\n"
        
        documents.append(TempDocObject(description, {'city': itinerary['city'], 'url': itinerary['url']}))

    return documents

def upload(documents, batch_size=50):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        try:
            qdrant_client.upload_records(
                collection_name="itineraries_data",
                records=[
                    models.Record(
                        id=i + idx, 
                        vector=encoder.encode(doc.page_content).tolist(), 
                        payload={'content': doc.page_content, 'metadata': doc.metadata}
                    )
                    for idx, doc in enumerate(batch)
                ],
            )
            print(f"Uploaded batch {i // batch_size + 1}/{(len(documents) // batch_size) + 1}")
        except Exception as e:
            print(f"Error uploading batch {i // batch_size + 1}: {e}")


# Process and upload the itineraries JSON file
upload(process_json('./data/itineraries.json'))
