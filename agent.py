

from mesa import Agent
from mesa.experimental.cell_space import CellAgent, FixedAgent


from colors import ROAD_COLOR, BUS_STOP_COLOR, BUILDING_COLOR, AGENT_COLOR, BUS_COLOR

class BuildingAgent(FixedAgent):
    color = BUILDING_COLOR
    def __init__(self, model):
        super().__init__(model)

class RoadAgent(FixedAgent):
    color = ROAD_COLOR
    def __init__(self, model):
        super().__init__(model)

class BusStopAgent(FixedAgent):
    color = BUS_STOP_COLOR
    def __init__(self, model):
        super().__init__(model)

class BusAgent(Agent):
    color = BUS_COLOR
    def __init__(self, model, *args, **kwargs):
        super().__init__(model, *args, **kwargs)

class EmployeeAgent(Agent):
    color = AGENT_COLOR
    def __init__(self, model, *args, **kwargs):
        super().__init__(model, *args, **kwargs)

        self.home = None
        self.wealth = 0 
        self.income = None
        self.needs = None

