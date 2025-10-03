import base64
import os
from groq import Groq
from dotenv import load_dotenv
from compress_img import ImageCompression

class ImageToDesc:
    def __init__(self, img):
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key)
        self.url = f"data:image/jpeg;base64,{img}"
        if os.path.exists(self.url):  # Check if it's a file path
            if os.path.getsize(self.url) > 20 * 1024 * 1024:
                img = ImageCompression.encode_image(img)
                print("this sucks")
        self.img = img
        
        self.prompt = self.create_prompt()
        self.desc = self.generate_response().replace("\n", "").replace("  ", " ").replace("*", "")
    @staticmethod
    def is_base64(s):
        try:
            base64.b64decode(s, validate=True)
            return True
        except base64.binascii.Error:
            return False

    def create_prompt(self):
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": '''Please analyze the provided image and generate a detailed, objective description of its contents. Focus on accurately identifying and describing the following elements:
                        - Primary objects or subjects present
                        - Their physical characteristics (e.g., size, color, shape)
                        - Their spatial relationships and positions within the scene
                        - Notable actions or interactions occurring
                        - The setting or environment, including background details or time of day
                        Avoid subjective interpretations or unnecessary elaboration; aim for a factual and precise depiction of the image's content.'''
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{self.img}"
                        }
                    }
                ]
            }
        ]

    def generate_response(self):
        retries = 3
        delay = 5  # seconds

        for attempt in range(retries):
            try:
                completion = self.client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=self.prompt,
                    temperature=0.5,
                    max_completion_tokens=1024,
                    top_p=1,
                    stream=False
                )
                return completion.choices[0].message.content

            except Exception as e:
                if "429" in str(e):  # Handle rate limiting
                    return "Limit Exceeded"
                elif "400" in str(e):
                    raise e
                else:
                    raise e