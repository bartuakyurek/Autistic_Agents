"""

A basic interface to declare a 2D city map and request path lengths
given a starting and a target point coordinate on the map. This map
is a binary map where 0 indicates a movable tile, and 1 indicates 
an obstacle. 

MAPF benchmarks https://movingai.com/benchmarks/mapf/index.html
are supported in the initialization of the city grid. 

WARNING: .map files in MAPF benchmarks are assumed to consist of only
@ and . characters where @ is an obstacle and . is a free cell.


@author: bartu
@date: Spring 2025
"""


import numpy as np
import heapq

class City:
    def __init__(self, width=30, height=30, map_array=None):
        # Warning: Map array is assumed to be consisting of 0 and 1s
        # where 0 means movable cell and 1 means obstacle cell.
        if map_array is not None:
            self.grid = np.array(map_array)
            self.width, self.height = self.grid.shape
        else:
            self.width = width
            self.height = height
            self.grid = np.zeros((width, height))  # 0: free, 1: obstacle

    def get_free_cell_coords(self, grid=None, free_value=0):
        """
        Returns a list of (row, col) coordinates where the grid value equals `free_value`.
        """
        if grid is None:
            grid = self.grid

        coords = np.argwhere(grid == free_value)
        return [tuple(coord) for coord in coords]  

    def in_bounds(self, coord):
        x, y = coord
        return 0 <= x < self.width and 0 <= y < self.height

    def is_free(self, coord):
        x, y = coord
        return self.grid[x, y] == 0

    def neighbors(self, coord):
        x, y = coord
        candidates = [(x-1,y), (x+1,y), (x,y-1), (x,y+1)]
        return [n for n in candidates if self.in_bounds(n) and self.is_free(n)]

    def get_estimated_path_cost(self, start, target):
        assert self.in_bounds(start) and self.in_bounds(target), f"Coordinates out of bounds"
        return abs(start[0] - target[0]) + abs(start[1] - target[1])  # Manhattan

    def shortest_path(self, start, target):
        assert self.in_bounds(start) and self.in_bounds(target), "Start or target out of bounds"
        assert self.is_free(start) and self.is_free(target), "Start or target is blocked"

        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while frontier:
            _, current = heapq.heappop(frontier)

            if current == target:
                break

            for next in self.neighbors(current):
                new_cost = cost_so_far[current] + 1  # cost to move = 1
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.get_estimated_path_cost(next, target)
                    heapq.heappush(frontier, (priority, next))
                    came_from[next] = current

        if target not in came_from:
            return None  # No path found

        # Reconstruct path
        path = []
        curr = target
        while curr != start:
            path.append(curr)
            curr = came_from[curr]
        path.append(start)
        path.reverse()
        return path

    def get_shortest_path_length(self, start, target):
        path = self.shortest_path(start, target)
        return len(path) if path else float('inf')


if __name__ == '__main__':
    import os 
    import random
    from io_handler import get_binary_map
    mapname = 'maze-128-128-10.map'
    mapfile_path = os.path.join(os.path.dirname(__file__), 'assets', mapname)
    binary_grid = get_binary_map = get_binary_map(mapfile_path=mapfile_path)
    print("Map loaded\n:", binary_grid)

    city = City(map_array=binary_grid)
    available_cells = city.get_free_cell_coords(grid=binary_grid)
   
    start = random.choice(available_cells)
    target = random.choice(available_cells)
    
    print("Start: ", start)
    print("Target: ", target)

    estimated = city.get_estimated_path_cost(start, target)
    shortest = city.get_shortest_path_length(start, target)

    print("Manhattan distance: ", estimated)
    print("Shortest path: ", shortest)

