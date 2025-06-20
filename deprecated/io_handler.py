
from PIL import Image
import numpy as np

from unused.colors import ROAD_COLOR, BUS_STOP_COLOR, BUILDING_COLOR
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


def load_city(image_path, road_color=ROAD_COLOR, station_color=BUS_STOP_COLOR, building_color=BUILDING_COLOR):
    # Black pixels in the image are treated as roads
    # Return the coordinates available to vehicles
    road_pixels = load_entity_pixels(image_path, road_color)
    station_pixels = load_entity_pixels(image_path, station_color)
    building_pixels = load_entity_pixels(image_path, building_color)

    return road_pixels, station_pixels, building_pixels

def get_image_width_height(image_path):
    img = Image.open(image_path).convert("RGB")  # Ensure RGB format
    data = np.array(img)
    return data.shape[0], data.shape[1]


if __name__ == '__main__':
    image_path = "./assets/simple_10_10.png"  # replace with your image path
    road_pixels, station_pixels, building_pixels = load_city(image_path)
    print("Road pixels:\n", road_pixels)
    print("Building pixels:\n", building_pixels)
    print("Station pixels:\n", station_pixels)
