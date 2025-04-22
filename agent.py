

from mesa import Agent
from mesa.experimental.cell_space import CellAgent, FixedAgent


from colors import ROAD_COLOR, BUS_STOP_COLOR, BUILDING_COLOR, AGENT_COLOR, BUS_COLOR


#######################################################################################################################
# Static Agents -----------------------------------------------------------------------------------------------
#######################################################################################################################
# These aren't autonomous agents but entities that
# agents can interact. They are declared as Agents for 
# Mesa's grid placement purposes.
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

#######################################################################################################################
# Transportation Agents -----------------------------------------------------------------------------------------------
#######################################################################################################################
class BusAgent(Agent):
    color = BUS_COLOR
    def __init__(self, model, stations=None, *args, **kwargs):
        super().__init__(model, *args, **kwargs)
        self.route = []
        self.stations = []
        self.current_index = 0
        self.next_station = 0

        if stations: self.assign_route(stations)

    def assign_route(self, stations):
        assert len(stations) >= 2, f"Expected at least 2 stations, got {len(stations)}."
        self.stations = stations
        self.next_station = stations[1]

        # TODO: update self.route based on A*
                
    def step(self):
        if self.current_index >= len(self.route):
            self.remove() # Bus agent is removed at the end of its route 

#######################################################################################################################
# Employee Agents -----------------------------------------------------------------------------------------------
#######################################################################################################################
class EmployeeAgent(Agent):
    color = AGENT_COLOR
    def __init__(self, model, *args, **kwargs):
        super().__init__(model, *args, **kwargs)

        self.home = None
        self.wealth = 0 
        self.income = None
        self.needs = None

class AutisticEmployee(EmployeeAgent):
    pass
class AllisticEmployee(EmployeeAgent):
    pass


#######################################################################################################################
# ---------------------------------------------------------------------------------------------------------------------
#######################################################################################################################