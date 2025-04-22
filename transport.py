


class Bus:
    def __init__(self, ID):
        self.route = []
        self.ID = ID
        self.stations = []
        self.current_index = 0
        self.next_station = 0

    def assign_route(self, stations):
        assert len(stations) >= 2, f"Expected at least 2 stations, got {len(stations)}."
        self.stations = stations
        self.next_station = stations[1]

    def move_to_next(self):
        pass