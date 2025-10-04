# from image_metadata import ImageMetadata
from openai import OpenAI
from image_metadata import ImageMetadata
from image_to_desc import ImageToDesc

class ImageToBlog:
    def __init__(self):
        self.client = OpenAI()
        self.prompt = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": '''Given a sequence of timestamps, locations, and corresponding image descriptions in order, write a natural and engaging first-person travel blog. Keep the tone conversational and informative—like a real traveler sharing experiences rather than a scripted story.  
                        
                        - Use the visual and locational context from the images to add relevant details.  
                        - If the location is an address, refer to the nearest well-known landmark or place of interest instead.  
                        - Instead of exact times, describe the general time of day (e.g., 'early morning,' 'sunset,' or 'late at night') and ensure the blog flows naturally in chronological order.  
                        - Focus on real observations, thoughts, and experiences rather than generic travel clichés or overly poetic descriptions.'''  
                    }
                ]
            }
        ]
        self.merge_prompt = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": '''The following are two blog entries about the same locations, events, or stories. Rearrange and tune the second to output an article with the ordered geographical accuracy of the first. Make minimal language changes--keep excerpts of the exact awkward phrasing and humanness of the second.'''  
                    }
                ]
            }
        ]
        self.fine_tune_response = ""
        self.openai_response = ""
        self.response = ""

        self.few_shots = [
                {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": '''Below are some blog posts written by user. Read these examples carefully to understand the voice, tone, and style. Notice how the language is personal, conversational, and rich in detail. Your task is to rewrite a new blog post that mirrors this style exactly.'''  
                    },
                    {
                        "type": "text",
                        "text": '''Using the style and voice of the above examples, rewrite the blog post below, making minimal changes. Ensure that your response:

                        -Is written in a warm, engaging, and human tone.
                        -Mimics the sentence structure, word choice, and rhythm of the examples.
                        -Includes personal insights or historical/introspective anecdotes if appropriate.
                        -Has detailled and informative descriptions at each stop, practical recommendations or suprising reflection.
                        -Remains authentic and true to the voice demonstrated in the provided blogs.
                        -Paced leisurely, stream-of-consciousness, and unlyrically.'''  
                    }
                ]
            }
        ]
    def add_images(self): #, paths):
        paths = ["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg"]
        for path in paths:
            img = ImageMetadata(path)
            descr = ImageToDesc(img.img).desc
            self.prompt[0]["content"].append({"type": "text", "text": descr})
            if img.loc and img.time:
                self.prompt[0]["content"].append({"type": "text", "text": f"The previous image was taken at location {img.loc} at time {img.time}"})
            elif img.loc:
                self.prompt[0]["content"].append({"type": "text", "text": f"The previous image was taken at location {img.loc}"})
            elif img.time:
                self.prompt[0]["content"].append({"type": "text", "text": f"The previous image was taken at time {img.time}"})
    
    def add_images(self, imgs):
        for img in imgs.values():
            descr = ImageToDesc(img.img).desc
            self.prompt[0]["content"].append({"type": "text", "text": descr})
            if img.loc and img.time:
                self.prompt[0]["content"].append({"type": "text", "text": f"The previous image was taken at location {img.loc} at time {img.time}"})
            elif img.loc:
                self.prompt[0]["content"].append({"type": "text", "text": f"The previous image was taken at location {img.loc}"})
            elif img.time:
                self.prompt[0]["content"].append({"type": "text", "text": f"The previous image was taken at time {img.time}"})

    def generate_response(self):
        response = self.client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:personal:imageto-itin-v6:BGVLjpTy",
            messages=self.prompt,
        )

        self.fine_tune_response = response.choices[0].message.content
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.prompt,
        )

        self.openai_response = response.choices[0].message.content
    
    def merge_responses(self):
        self.merge_prompt[0]["content"].append({"type": "text", "text": self.openai_response})
        self.merge_prompt[0]["content"].append({"type": "text", "text": self.fine_tune_response})
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.merge_prompt,
        )
        self.response = response.choices[0].message.content
