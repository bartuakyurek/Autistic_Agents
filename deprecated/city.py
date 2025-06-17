
import numpy as np
from typing import Tuple
from mesa import Model
from mesa.space import MultiGrid

import seaborn as sns
import matplotlib.pyplot as plt

from unused.agent import *
from unused.io_handler import load_city, get_image_width_height


class City(Model):
    # From Mesa Documentation:
    # The model can be visualized as a list containing all the agents. 
    # The model creates, holds and manages all the agent objects, specifically in a dictionary. 
    # The model activates agents in discrete time steps.
    def __init__(self, image_path, *args, seed = None, rng = None, **kwargs):
        super().__init__(*args, seed=seed, rng=rng, **kwargs)

        city_entities_tuple = load_city(image_path)
        self._validate_citymap(city_entities_tuple)
        
        self.width, self.height = get_image_width_height(image_path)
        self.grid = MultiGrid(self.width, self.height, torus=False)

        road_pixels, busstop_pixels, building_pixels =  city_entities_tuple # WARNING: Make sure order stays the same
        self.place_fixed_agent(RoadAgent, road_pixels)
        self.place_fixed_agent(BuildingAgent, building_pixels)
        self.place_fixed_agent(BusStopAgent, busstop_pixels)

    def place_fixed_agent(self, AgentType, pixels):
        # Create agents
        n = len(pixels)
        road_agents = AgentType.create_agents(model=self, n=n)
        # Create x and y positions for agents
        x = pixels[:,0] 
        y = pixels[:,1]
        for a, i, j in zip(road_agents, x, y):
            self.grid.place_agent(a, (i, j))

    def _validate_citymap(self, entity_tuple : Tuple[np.ndarray]):
        # Each array holds coordinates with shape [num_cells_occupied_by_entity, 2]
        # There should be a single entity in each cell, i.e.
        # a road cell cannot be on the same cell with a building cell
        self.__busy_cells = []
        for entity in entity_tuple:
            for location in entity:
                if any(np.array_equal(location, loc) for loc in self.__busy_cells):
                    raise ValueError("A cell cannot be occupied with multiple non-agent entities")
                self.__busy_cells.append(location)


def visualize_city(city : Model):
    # WARNING: at this point it colors only one entities but there could be more than one (e.g. Agent sitting on a Road) 
    content_id_grid = np.zeros((city.grid.width, city.grid.height))
    for cell_content, (x, y) in city.grid.coord_iter():
      
        if len(cell_content):
            ag = cell_content[0]
        else:
            ag = None
        if isinstance(ag, EmployeeAgent): 
            content_id = 5
        elif isinstance(ag, BuildingAgent):
            content_id = 10
        elif isinstance(ag, BusStopAgent):
            content_id = 20
        elif isinstance(ag, RoadAgent):
            content_id = 30
        elif isinstance(ag, BusAgent):
            content_id = 50
        else:
            content_id = 0 # Empty

        content_id_grid[x][y] = content_id

    # Plot using seaborn, with a visual size of 5x5
    g = sns.heatmap(content_id_grid, cmap="viridis", annot=True, cbar=False, square=True)
    g.figure.set_size_inches(5, 5)
    g.set(title="each number represents content id")

    plt.show()

if __name__ == '__main__':
    
    image_path = "./assets/simple_10_10.png"  
    city = City(image_path=image_path)

    visualize_city(city)
    