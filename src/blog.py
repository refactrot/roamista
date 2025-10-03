class Blog:
    def __init__(self, city : str, text : str, images : list, url : str):
        self.city = city
        self.text = text
        self.images = images
        self.url = url
        self.pois = []
    
    def __str__(self):
        return "URL: " + self.url + "Text Content: \n" + self.text + "\nNumber of Images: " + str(len(self.images)) + "Extracted POIS: " + self.pois
    
    @staticmethod
    def load_blog(raw_blog : dict):
        if "error" in raw_blog:
            return Blog(city, None, None, url)
        url = raw_blog["url"]
        text = raw_blog["text_content"]
        all_images = raw_blog["images"]
        city = raw_blog["city"]
        images = []
        for image in all_images:
            images.append(image)
        list(images)
        return Blog(city, text, images, url)