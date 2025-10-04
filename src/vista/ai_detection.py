import requests
from dotenv import load_dotenv
import os

class AIDetection:
    def getPercentage(text):
        load_dotenv()
        SAPLING_API_KEY = os.getenv("GROQ_API_KEY")
        response = requests.post(
            "https://api.sapling.ai/api/v1/aidetect",
            json={
                "key": "YYBVJG8W61SZVTGZWLVT031R90EO1QRT",
                "text": f"{text}"
            }
        )

        raw = response.json()
        return raw#["score"]