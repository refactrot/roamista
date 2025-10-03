from PIL import Image
import io
import base64

class ImageCompression:
    @staticmethod
    def encode_image(img_path, max_size=(1024, 1024), quality=85, max_attempts=10):
        attempt = 0
        while attempt < max_attempts:
            # Load the image
            with Image.open(img_path) as img:
                # Resize the image (preserve aspect ratio)
                img.thumbnail(max_size, Image.ANTIALIAS)

                # Compress and save to a buffer
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=quality)

                # Check if the image size fits within the limit
                if buffer.tell() <= 20 * 1024 * 1024:  # 20MB limit
                    break
                
                # Reduce quality and/or size further if the limit is exceeded
                quality -= 5  # Reduce quality by 5 percent for each iteration
                max_size = tuple(int(dim * 0.9) for dim in max_size)  # Reduce size by 10% each attempt

                attempt += 1

            # If we reached the max_attempts without success, raise an error
            if attempt == max_attempts:
                raise ValueError("Image could not be compressed to fit within 20MB after multiple attempts.")

            # Encode the image to base64
            encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return encoded_image

        return None