"""

Simulation script for needs-based model given in Aguilera et al. It runs the 
simulation and saves the resulting plots under /results/<policy_name> where
available policy names are: fixed, free, and flexible.

This project aims to simulate commute-related challenges of Autistic people
and tries to mitigate the effects of these challenges on wealth distribution
by employing alternative workplace policies.


WARNING: needs-based model implemented here have important amendments 
that affect the simulation outcome in the end. Please see the report
for detailed description.

@author: bartu
@date: Spring 2025
"""


import random
import matplotlib.pyplot as plt
import logging
import os

from city import City
from agent import Agent

# Read config.yaml for simulation parameters
import yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

DAY_LENGTH = config['simulation']['day_length']
MAX_TICKS = config['simulation']['max_ticks']
NUM_AGENTS = config['simulation']['num_agents']
BUS_PRICE = 0.005

# For logging
_TIME = 0 
logger = logging.getLogger(__name__)
logging.basicConfig(filename='simulation.log', encoding='utf-8', filemode='w', level=logging.INFO)


def get_workplaces(policy):
    workplaces = []
    for wp in config["workplace_locations"]:
        assert wp in config["policy"], f"Please specify policy for workplace {wp} in config.yaml under policy section."
        if policy == config["policy"][wp]:
            workplaces.append(wp)
    
    if len(workplaces) == 0:
        raise ValueError(f"No workplace found with policy {policy}. Consider adding it in config.yaml under policy section.")
    return workplaces

def get_policy_colors(policy):
    if policy == "fixed":
        return "gray"
    elif policy == "free":
        return "cyan"
    elif policy == "flex":
        return "pink"
    else:
        print(f"WARNING: Undefined color for policy: {policy}")
        return "pink"


def prepare_results_path(policy):
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)

    policy_results_dir = os.path.join(results_dir, policy)
    os.makedirs(policy_results_dir, exist_ok=True)
    return policy_results_dir

def setup_agents(city):
    
    available_homes = [k for k in config["houses"].keys()]
    available_workplaces = get_workplaces(policy=POLICY)  # For the experiments only get the workplaces with the same policy
    available_tolerances = [i+1 for i in range(7)]
    print("Available workplaces: ", available_workplaces)
    print("Available houses: ", available_homes)
    #available_cells = city.get_free_cell_coords()
    
    agents = []
    for i in range(NUM_AGENTS):
        a = Agent(name="A"+str(i), 
                  city=city,
                  home=random.choice(available_homes),
                  workplace=random.choice(available_workplaces),
                  social_tolerance=random.choice(available_tolerances)
                ) 
        agents.append(a)
    return agents

def load_simulation_map(assetspath='assets', mapname = 'maze-128-128-10.map'):
    from io_handler import get_binary_map

    mapfile_path = os.path.join(os.path.dirname(__file__), assetspath, mapname)
    binary_grid = get_binary_map = get_binary_map(mapfile_path=mapfile_path)
    print("Map loaded\n:", binary_grid)

    city = City(map_array=binary_grid)
    return city

            
    
if __name__ == "__main__":
    import os 
    import random

    from plot import plot_wealth_distribution, plot_relations

    RANDOMIZE_WALK = True # Randomly choose walk costs
    if RANDOMIZE_WALK: 
        city = None
    else:
        city = load_simulation_map()

    policies = ["fixed", "free", "flex"] #  Options: ["fixed", "free", "flex"] 
    for POLICY in policies:
        print("Chosen policy: ", POLICY)
        agents = setup_agents(city)

        # Simulate
        for t in range(MAX_TICKS):
            for agent in agents:
                logger.info(f'[{t}] Time step ------------')
                agent.deliberate_action(t)
                agent.decay_needs_sat() # Water tank model, decay needs

        # Plot policy results
        res_path = prepare_results_path(POLICY)
        plot_wealth_distribution(agents, title=f"Policy: {POLICY}", color=get_policy_colors(POLICY), save=True, results_dir=res_path)
        plot_relations(agents, lambda a: a.social_tolerance, lambda a: a.final_wealth(), xlabel="tolerance", ylabel="wealth", title="Social Tolerance vs. Wealth", results_dir=res_path)
        plot_relations(agents, lambda a: a.social_tolerance, lambda a: a.social_burnout_sum,  xlabel="tolerance", ylabel="social-burnout", title="Social Tolerance vs. Social Burnout Rate", results_dir=res_path)
        plot_relations(agents, lambda a: a.social_tolerance, lambda a: a.energy_burnout_sum,  xlabel="tolerance", ylabel="energy-burnout",  title="Social Tolerance vs. Energy Burnout Rate", results_dir=res_path)
        plot_relations(agents, lambda a: a.social_burnout_sum, lambda a: a.final_wealth(),  xlabel="social-burnout", ylabel="wealth",  title="Social Burnout Rate vs. Wealth", results_dir=res_path)
