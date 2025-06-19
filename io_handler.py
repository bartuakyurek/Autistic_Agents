import numpy as np

def read_map_file(filepath, return_arr=True):
    # Read .map file
    # If return_arr, returns a numpy array
    # otherwise return a list
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Skip header lines (WARNING: assumed to be first 4)
    lines = [line.strip() for line in lines if line.strip()] 
    grid_lines = lines[4:]
    grid = [list(line) for line in grid_lines]

    height = int(lines[1][len("height "):])
    width = int(lines[1][len("width "):])
    grid_arr = np.array(grid)
    assert grid_arr.shape == (height, width), f"Expected grid to have shape ({height},{width}), got {grid_arr.shape}"

    if return_arr: return grid_arr
    return grid

def get_binary_map(mapfile_path, free_sym=0, blocked_sym=1):
    # Read a .map file and replace free and blocked symbols 
    # with free_sym and blocked_sym
    grid = read_map_file(filepath=mapfile_path, return_arr=True)

    binary_map = np.zeros_like(grid, dtype=int)
    binary_map[grid == '.'] = free_sym
    binary_map[grid == '@'] = blocked_sym

    return binary_map



if __name__ == '__main__':
    import os 

    mapname = 'maze-128-128-10.map'
    mapfile_path = os.path.join(os.path.dirname(__file__), 'assets', mapname)

    map_grid = read_map_file(mapfile_path)
    print(map_grid)  # Print first row

    binary_grid = get_binary_map = get_binary_map(mapfile_path=mapfile_path)
    print(binary_grid)


