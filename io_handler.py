
from PIL import Image
import numpy as np

BLACK =  [0, 0, 0]

def load_roadmap(image_path, road_color=BLACK)->np.ndarray:
    # Black pixels in the image are treated as roads
    # Return the coordinates available to vehicles

    img = Image.open(image_path).convert("RGB")  # Ensure RGB format
    data = np.array(img)
    road_pixels = np.argwhere(np.all(data == road_color, axis=-1))
    return road_pixels



if __name__ == '__main__':
    image_path = "./assets/simple_10_10.jpg"  # replace with your image path
    load_roadmap(image_path=image_path)