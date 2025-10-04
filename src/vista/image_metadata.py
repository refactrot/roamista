from PIL import Image
import os
from dotenv import load_dotenv
import piexif
import requests
import base64
import requests

class ImageMetadata:
    def __init__(self, path):
        load_dotenv()
        self.api_key = os.getenv("GEOCODIFY_API_KEY")
        self.path = path
        self.lat, self.lon, self.time = ImageMetadata.get_lat_lon_time_from_exif(self.path)
        self.loc = ImageMetadata.reverse_geocode(self.lat, self.lon, self.api_key)
        self.img = ImageMetadata.encode_image(self.path)

    def get_geotagging(exif_data):
        """Extract GPS info from EXIF data."""
        if "GPS" in exif_data:
            return exif_data["GPS"]
        return None

    def convert_to_degrees(value):
        """Convert GPS coordinates from EXIF format to degrees."""
        d, m, s = value
        return d[0] / d[1] + (m[0] / m[1]) / 60.0 + (s[0] / s[1]) / 3600.0

    def get_lat_lon_time_from_exif(image_path):
        """Extract latitude, longitude, and timestamp from image EXIF metadata."""
        image = Image.open(image_path)
        try:
            exif_data = piexif.load(image.info['exif'])
        except:
            return None, None, None
        # Extract GPS data
        gps_info = ImageMetadata.get_geotagging(exif_data)
        lat, lon = None, None
        if gps_info:
            lat = ImageMetadata.convert_to_degrees(gps_info[2]) if 2 in gps_info else None  # Latitude
            lon = ImageMetadata.convert_to_degrees(gps_info[4]) if 4 in gps_info else None  # Longitude

            # Adjust for N/S and E/W
            if gps_info.get(3) == b'S':  # South
                lat = -lat
            if gps_info.get(1) == b'W':  # West
                lon = -lon

        # Extract DateTimeOriginal (when the photo was taken)
        timestamp = None
        if piexif.ExifIFD.DateTimeOriginal in exif_data["Exif"]:
            timestamp = exif_data["Exif"][piexif.ExifIFD.DateTimeOriginal].decode("utf-8")

        return lat, lon, timestamp
    

    def reverse_geocode(lat, lon, api_key):
        """Finds the place name for the given coordinates using Geocodify's Reverse Geocoding API."""
        url = f"https://api.geocodify.com/v2/reverse?api_key={api_key}&lat={lat}&lng={lon}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('response') and data['response'].get('features'):
                place_name = data['response']['features'][0]['properties'].get('name', 'Unnamed Place')
                return place_name
            else:
                return 'No place found nearby'
        else:
            return f"Error: {response.status_code}"
        
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")