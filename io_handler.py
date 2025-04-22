
from PIL import Image
import numpy as np

BLACK =  np.array([0, 0, 0])
GREEN = np.array([0, 255, 0]) 
ORANGE = np.array([255, 153, 51])
color_tolerance = 20  # allowed difference per channel

def load_entity_pixels(image_path, target_color)->np.ndarray:
    # Return the coordinates in a grid 
    # colored in target_color
    img = Image.open(image_path).convert("RGB")  # Ensure RGB format
    data = np.array(img)
    
    # Compute distance from each pixel to the target color
    diff = np.abs(data - target_color)
    mask = np.all(diff <= color_tolerance, axis=-1)  # True where pixel is a road

    entity_pixels = np.argwhere(mask)
    return entity_pixels


def load_city(image_path, road_color=BLACK, station_color=ORANGE, building_color=GREEN):
    # Black pixels in the image are treated as roads
    # Return the coordinates available to vehicles
    road_pixels = load_entity_pixels(image_path, road_color)
    station_pixels = load_entity_pixels(image_path, station_color)
    building_pixels = load_entity_pixels(image_path, building_color)

    return road_pixels, station_pixels, building_pixels


if __name__ == '__main__':
    image_path = "./assets/simple_10_10.png"  # replace with your image path
    road_pixels, station_pixels, building_pixels = load_city(image_path)
    print("Road pixels:\n", road_pixels)
    print("Building pixels:\n", building_pixels)
    print("Station pixels:\n", station_pixels)
