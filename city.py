
from mesa.space import MultiGrid

class City(MultiGrid):
    def __init__(self, 
                 width : int, 
                 height : int, 
                 torus : bool, 
                 property_layers = None):
        super().__init__(width, height, torus, property_layers)

        