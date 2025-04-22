
import numpy as np
from mesa.space import MultiGrid

from io_handler import load_city, get_image_width_height
from typing import Tuple, List

class City(MultiGrid):
    def __init__(self, 
                 citymap_png_path,
                 torus : bool = False, # Treat grid as a torus
                 verbose : bool = False,
                 ):
        self.__busy_cells = []
        city_entities_tuple = load_city(citymap_png_path)
        self._validate_citymap(city_entities_tuple)
        
        width, height = get_image_width_height(citymap_png_path)
        super().__init__(width, height, torus)

        if verbose: print(f"[INFO] City grid created with {width}x{height} dimensions.")
        self.verbose = verbose


    def _validate_citymap(self, entity_tuple : Tuple[np.ndarray]):
        # an entity is an array of cells occupied by that entity type
        # e.g. roads, buildings, bus stations
        # np.ndarray holds coordinates for each instance with shape [num_cells, 2]
        #
        # There should be a single entity in each cell
        # i.e. a road cell cannot be on the same cell with a building cell
        for entity in entity_tuple:
            for location in entity:
                if any(np.array_equal(location, loc) for loc in self.__busy_cells):
                    raise ValueError("A cell cannot be occupied with multiple non-agent entities")
                self.__busy_cells.append(location)
        
        

if __name__ == '__main__':

    image_path = "./assets/simple_10_10.png"  

    city = City(image_path, verbose=True)