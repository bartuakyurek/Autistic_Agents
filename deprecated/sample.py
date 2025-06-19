class CityGrid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]  # 2D grid of cells

    def add_entity(self, entity, x, y):
        self.grid[y][x] = entity  # Place an agent/bus on the grid

    def remove_entity(self, entity, x, y):
        self.grid[y][x] = None  # Remove an entity from the grid

    def get_nearby_buses(self, x, y):
        buses = []
        # Check adjacent cells for buses
        for dx in range(-1, 2):  # Look 1 cell in each direction
            for dy in range(-1, 2):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    cell = self.grid[ny][nx]
                    if isinstance(cell, Bus):  # Check if it's a bus
                        buses.append(cell)
        return buses

class Bus:
    def __init__(self, bus_id, route, capacity, crowd_level):
        self.bus_id = bus_id
        self.route = route  # Predefined route (list of coordinates)
        self.capacity = capacity  # Max number of passengers
        self.crowd_level = crowd_level  # Current crowd level (low, medium, high)

    def update_crowd_level(self, num_passengers):
        # Example: Update crowd level based on passengers
        if num_passengers < self.capacity * 0.3:
            self.crowd_level = 'low'
        elif num_passengers < self.capacity * 0.7:
            self.crowd_level = 'medium'
        else:
            self.crowd_level = 'high'

class Agent:
    def __init__(self, agent_id, x, y):
        self.agent_id = agent_id
        self.x = x
        self.y = y

    def move(self, new_x, new_y, city_grid):
        # Move the agent to a new position and update the grid
        city_grid.remove_entity(self, self.x, self.y)
        self.x = new_x
        self.y = new_y
        city_grid.add_entity(self, new_x, new_y)

    def find_buses(self, city_grid):
        # Query the grid for nearby buses
        buses = city_grid.get_nearby_buses(self.x, self.y)
        return buses

    def decide_to_board(self, buses):
        # Decide whether to board a bus based on crowd levels
        for bus in buses:
            if bus.crowd_level == 'low':
                return bus  # Board the bus
        return None  # Don't board any bus

# Example usage
city = CityGrid(10, 10)
agent = Agent(agent_id=1, x=2, y=2)
bus = Bus(bus_id=1, route=[(0, 0), (0, 1), (0, 2)], capacity=10, crowd_level='medium')

city.add_entity(agent, 2, 2)
city.add_entity(bus, 3, 2)

buses_nearby = agent.find_buses(city)
boarded_bus = agent.decide_to_board(buses_nearby)
if boarded_bus:
    print(f"Agent {agent.agent_id} boarded bus {boarded_bus.bus_id}.")
else:
    print(f"Agent {agent.agent_id} didn't board any bus.")
