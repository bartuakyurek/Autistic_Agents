

from mesa import Agent
from mesa.experimental.cell_space import CellAgent, FixedAgent

from io_handler import BLACK, ORANGE, GREEN

class BuildingAgent(FixedAgent):
    color = GREEN
    def __init__(self, model):
        super().__init__(model)

class RoadAgent(FixedAgent):
    color = BLACK
    def __init__(self, model):
        super().__init__(model)

class BusStopAgent(FixedAgent):
    color = ORANGE
    def __init__(self, model):
        super().__init__(model)


class EmployeeAgent(Agent):
    def __init__(self, model, *args, **kwargs):
        super().__init__(model, *args, **kwargs)

        self.home = None
        self.wealth = 0 
        self.income = None
        self.needs = None