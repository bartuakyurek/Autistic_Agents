import random
import matplotlib.pyplot as plt
import numpy as np
import logging
import copy 
import os

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


def get_building_coords(building : str):
    # TODO: UNUSED - Walking currently takes random effects, it should be scaled with distance in the upcoming commits
    if building[:4] == "home":
        return config['houses'][building]
    elif building[:4] == "work":
        return config['workplace_locations'][building]
    else:
        raise ValueError(f"Unknown building name: {building}. Please make sure this building is either declared in .yaml or implemented correctly in if-else above")
    
def _get_crowd_cost(tolerance, crowd=None):
    if crowd is None:
        crowd = int( random.random() * 10 )
        logger.warning(f"Crowd level not provided. Randomly chosen crowd level: {crowd}")

    return -(float(crowd ** 2)/float(tolerance+1e-12)) # 1e-12 to avoid division by zero
    
class Agent:
    def __init__(self, name, social_tolerance, home="home_0", workplace="workplace_0", income=5):
        self.name = name
        self.home = home
        self.workplace = workplace

        self.where = home
        self.wealth = float(0)
        self.TIMESTEP_INCOME = income
        self.in_recovery = False # True if in "meltdown"
        self.burnout_state = None
        self.recovery_timer = 0
        self.social_burnout_sum = 0
        self.energy_burnout_sum = 0

        self.NEED_CATEGORIES = {
        "energy": {"category": "physical", "max": 20, "timestep_multiplier":0.98},
        "alone_time": {"category": "psychological", "max": 10, "timestep_multiplier":1}, # no timestep_multiplier
        "socialization": {"category": "psychological", "max": 10, "timestep_multiplier":1}, # there's no "social" need, but here we lump friendship, family, intimacy
        "financial_security": {"category": "economic", "max": 10, "timestep_multiplier":1},  # no timestep_multiplier
        "self_esteem": {"category": "psychological", "max": 10, "timestep_multiplier":1}, # normally it belongs to "esteem" category, not social  
        }

        self.CATEGORY_IMPORTANCE = { # Equally important atm
            "physical": 1.0,
            "psychological": 1.0,
            "economic": 1.0
        }

        self.initial_needs = self.get_needs_dict(set_zero=False) # Init to max energy
        self.needs =  copy.deepcopy(self.initial_needs)

        self.social_tolerance = social_tolerance
        

    def get_needs_dict(self, set_zero=True):
        # This is where needs are defined 
        # If set_zero is True, then it sets
        # all needs entries to zero, that is used
        # to get an empty needs dict for action
        # effects update
        need_sat_levels = {}
        for key, item in self.NEED_CATEGORIES.items():
            if set_zero:
                need_sat_levels[key] = 0
            else:
                need_cap = item["max"]
                if need_cap is None:
                    need_sat_levels[key] = 0 # Assume: Need start at 0 if no max. cap, that is currently "wealth" need
                else:
                    need_sat_levels[key] = need_cap
        return need_sat_levels
    
    def _clamp_needs(self):
        # To prevent needs overshooting max capacity
        # In future work these maximum caps could be improved via training,
        # e.g. agent can choose to invest in some special training to improve
        # their social tolerance.
        for key, item in self.NEED_CATEGORIES.items():
            if item["max"] is not None:
                self.needs[key] = max(0, min(item["max"], self.needs[key]))

    def decay_needs_sat(self):
        # Need-Satisfaction Level decay, NSL_t (Eqn.1)
        # for a single time-step
        for n in self.needs:
            self.needs[n] = self.NEED_CATEGORIES[n]['timestep_multiplier'] * self.needs[n] # iterative

    def get_action_effect(self, action, **kwargs):
        # Need-Satisfaction Matrix
        # with amendments:
        # - entries in range [-inf, +inf] instead of [0,1]
        # - actions can have random effects instead of fixed scalars

        # Default effects
        needs_dict = self.get_needs_dict(set_zero=True)

        # Update costs based on action
        if action == "take_bus":
            crowd = kwargs["crowd"] if "crowd" in kwargs.keys() else None
            
            needs_dict["alone_time"] = _get_crowd_cost(tolerance=self.social_tolerance, crowd=crowd)
            needs_dict["energy"] = 0

            if self.where == self.home: # WARNING: Assumes take_bus means take_bus_to_workplace
                needs_dict["financial_security"] = +5 # Assumption: Taking bus has more financial security than walk because it has shorter path
        
        elif action == "walk":
            if "length" not in kwargs.keys(): 
                len = random.randint(1, 20) # This should be updated if you want to introduce other locations, e.g. a park to rest or actual bus stops
                logger.warning(f"No length is provided! Estimated length (RANDOM) {len}.") 
            else:
                len = kwargs["length"]
        
            needs_dict["energy"] = -len * 0.1
            needs_dict["alone_time"] = +1 

            if self.where == self.home:
                needs_dict["financial_security"] = +3 # WARNING: Assumes take_bus means take_bus_to_workplace
        
        elif action == "rest":
            needs_dict["energy"] = +0.2
            needs_dict["alone_time"] = +0.2

            if self.where == self.workplace:
                needs_dict["financial_security"] = -1

        elif action == "sleep":
            needs_dict["energy"] = +1
            needs_dict["alone_time"] = +1

            if self.where == self.workplace:
                needs_dict["financial_security"] = -5

        elif action == "work":
            social_factor =  +1 if random.random() < 0.5 else 0 # Potentially socialize during work

            needs_dict["energy"] = -2
            needs_dict["alone_time"] = -social_factor
            needs_dict["socialization"] = social_factor
            needs_dict["financial_security"]  = +5
        
        elif action == "wait":
            pass # No effect
        
        else:
            raise ValueError(f"Unrecognized action: {action}")
        
        return needs_dict

    def _check_burnout(self):
        # If low social energy, enter recovery
        if self.needs["alone_time"] <= 0:
            self.in_recovery = True
            self.recovery_timer = 5

            logger.info(f'[{_TIME}][BURNOUT] Agent {self.name} has social burnout.')
            self.burnout_state = "social"
            return True
        
        if self.needs["energy"] < 0: # Currently it is the same as social burnout
            self.in_recovery = True
            self.recovery_timer = 5

            logger.info(f'[{_TIME}][BURNOUT] Agent {self.name} has energy burnout.')
            self.burnout_state = "energy"
            return True

        return False

    def _recover_burnout_step(self):
        if self.burnout_state == "social":
            self.needs["alone_time"] += 0.1 * (self.social_tolerance + 0.1) # +epsilon to avoid multiply by zero, 0.1 results in linear increase in wealth outcome, larger values make them almost equal, this is tuned to make the impact of social tolerance higher
        elif self.burnout_state == "energy":
            self.needs["energy"] += 10 # Larger values make energy burnout easier to recover
        else:
            raise ValueError(f"Unrecognized burnout state: {self.burnout_state}")

        self.recovery_timer -= 1
        if self.recovery_timer <= 0:
            self.in_recovery = False
            return True # Recovery completed
        return False

    def get_fixed_policy_actions(self, time, location_str):
        if location_str == "home":
            if time % DAY_LENGTH < 10:
                return {"sleep", "rest"}
            elif time % DAY_LENGTH < 60: # TODO: how to define fixed and flexible work hours?
                return { "walk", "take_bus"} # Assumption: cannot sleep during work hours
            else:
                return {"sleep", "rest"}
       
        elif location_str == "work":
            if time % DAY_LENGTH < 20:
                return {"walk", "take_bus", "wait"} # Wait until shift starts
            elif time % DAY_LENGTH < 60: # TODO: how to define fixed and flexible work hours?
                return {"rest",  "work"} # Assumption: going back home not available during fixed work hours
            else:
                return {"walk", "take_bus"}
        else:
            raise ValueError(f"Unknown location string {location_str}")
        
    def get_free_policy_actions(self, time, location_str):
        if location_str == "home":
            return {"work", "sleep", "rest", "take_bus", "wait", "walk"} # Work from home available
        elif location_str == "work":
            return {"work", "sleep", "rest", "take_bus", "wait", "walk"} # Sleep at work available
        else:
            raise ValueError(f"Unknown location string {location_str}")

    def get_available_actions(self, time):
        # Valid actions (see get_action_effect()): 
        # take_bus, walk, rest, sleep, work

        # TODO-workplace policies comes here, i.e. you can only work at certain hours
        # and possibly you can only go to work 1-2 hours before work shift starts
        policy = config["policy"][self.workplace]

        # Home actions based on policy
        if self.where == self.home:
            if policy == "fixed":
                return self.get_fixed_policy_actions(time, "home")

            elif policy == "free":
                return self.get_free_policy_actions(time, "home")
            
            else:  
                logger.warning(f"Unknown policy {policy}")
                return {}
        
        # Workplace actions based on policy
        elif self.where == self.workplace:
            if policy == "fixed":
                return self.get_fixed_policy_actions(time, "work")
            
            elif policy == "free":
                return self.get_free_policy_actions(time, "work")

            else:  
                logger.warning(f"Unknown policy {policy}")
                return {}  
            
        # Undefined place
        else:
            logger.error(f"No actions available at {self.where}")
            return {}

    def compute_urgency(self, need_key):
        max_val = self.NEED_CATEGORIES[need_key]["max"]
        if max_val is None:
            return 0.1  # Minimal urgency for unbounded needs (do not set to 0)
        current_val = self.needs[need_key]
        return 1 - current_val / max_val

    def choose_action(self, time):

        best_score = float('-inf')
        best_action = None

        actions = self.get_available_actions(time)
        for action in actions:
            estimated_effects = self.get_action_effect(action) # WARNING: it is estimated because the action functions will call it again (so these estimated effects will not be used) 
            score = 0
            for need_key, delta in estimated_effects.items():
                category = self.NEED_CATEGORIES[need_key]["category"]
                importance = self.CATEGORY_IMPORTANCE.get(category, 1.0)
                urgency = self.compute_urgency(need_key)
                score += delta * urgency * importance 
            if score > best_score:
                best_score = score
                best_action = action

        logger.info(f"[ACT] Best action chosen: {best_action}")
        return best_action

    def deliberate_action(self, time):
        if self.in_recovery:
            logger.info(f"[BURNOUT] Agent {self.name} is in the recovery from {self.burnout_state} burnout... Accumulated social {self.social_burnout_sum } and {self.energy_burnout_sum} energy burnout scores.")
            self._recover_burnout_step()
            if self.burnout_state == "social": self.social_burnout_sum += 1
            if self.burnout_state == "energy": self.energy_burnout_sum += 1
            return
        
        if self._check_burnout(): # Enters recovery if needed
            return
       
        chosen_action = self.choose_action(time)
        
        effect = self.get_action_effect(chosen_action) # WARNING: choose_action() also calls this as estimated_effects, here we call it again because actions may have random effects
        self.apply_action(chosen_action, effect=effect)

        
    def _get_distance(self, start, end, type="manhattan"): 
        # TODO: should be A* with city grid, right now it assumes every cell is available and only computes manhattan dist
        if type == "manhattan":
            assert len(start) == 2 and len(end) == 2, f"Expected 2D coordinates, got start: {start} and end: {end}."
            return np.abs(start[0] - end[0]) + np.abs(start[1] - end[1])

    """
    def move_to(self, target:str):
        take_walk = False
        if self.where != target:
            if random.random() < 0.5:
                crowd = random.randint(0, 3)
                if crowd <= self.social_tolerance:
                    delta = self.get_action_effect("take_bus", crowd=crowd)
                    self.apply_action("take_bus", delta) # TODO: Better way to do it?
                    self.where = target
                else:
                    take_walk = True
            else:
                take_walk = True
            
            if take_walk:
                start_coord = get_building_coords(self.where)
                end_coord  =  get_building_coords(target)
                delta = self.get_action_effect("walk", length=self._get_distance(start_coord, end_coord))

                self.apply_action("walk", delta)
                self.where = target

    def do_work(self, hourly_income=5):
        if self.where == self.workplace:
            delta =  self.get_action_effect("work")
            self.apply_action("work", delta)
            self.wealth += hourly_income
        else:
            logger.warning(f"Agent can only work at {self.workplace}! Currently at {self.where}.")
       
    def rest(self):
        if self.where == self.home:
            self.apply_action("rest",  self.get_action_effect("rest"))
        else:
            logger.warning(f"Agent can only rest at {self.home}! Currently at {self.where}.")
    """

    def apply_action(self, action, effect):
        
        logger.info(f'[{_TIME}] Agent {self.name} takes action: {action} with effects {effect}. Current wealth: {self.wealth}')

        # Wealth effects of action
        if action == "work":
            # assert self.where == self.workplace, f"Expected to work at workplace"
            self.wealth += self.TIMESTEP_INCOME
        elif action == "take_bus":
            self.wealth -= BUS_PRICE
        
        # Relocate Agent
        if action == "take_bus" or action == "walk":
            self.where = self.workplace if self.where == self.home else self.home # WARNING: Assumes agent can only either at workplace or home

        assert len(effect) == len(self.needs), f"Please provide an array of effects with the same length of needs. Provided effect has length {len(effect)}, expected length {len(self.needs)}."
        for key in self.needs.keys():
            self.needs[key] += effect[key]
        
        logger.info(f"Current wealth: {self.wealth} and needs: {self.needs}")

        # Check for burnout before clamping needs
        if self._check_burnout():
            return

        self._clamp_needs()

    def final_wealth(self):
        return self.wealth
    
    def report(self):
        print(f"{self.name} final wealth: {self.final_wealth()}")
        # TODO: More attributes to report?

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
    else:
        print(f"WARNING: Undefined color for policy: {policy}")
        return "pink"

if __name__ == "__main__":
    # Setup agents
    POLICY = "free" # Options: "fixed", "free"

    available_homes = [k for k in config["houses"].keys()]
    available_workplaces = get_workplaces(policy=POLICY)  # For the experiments only get the workplaces with the same policy
    available_tolerances = [i+1 for i in range(7)]
    print("Chosen policy: ", POLICY)
    print("Available workplaces: ", available_workplaces)
    print("Available houses: ", available_homes)
    agents = []
    for i in range(NUM_AGENTS):
        a = Agent(name="A"+str(i), 
                     home=random.choice(available_homes),
                     workplace=random.choice(available_workplaces),
                    social_tolerance=random.choice(available_tolerances)
                 ) 
        agents.append(a)

    # Simulate
    for t in range(MAX_TICKS):
        for agent in agents:
            _TIME = t # For logging
            agent.deliberate_action(t)
            agent.decay_needs_sat() # Water tank model, decay needs

    from plot import plot_wealth_distribution, plot_relations
    plot_wealth_distribution(agents, title=f"Policy: {config["policy"][available_workplaces[0]]}", color=get_policy_colors(POLICY), save=True)
    plot_relations(agents, lambda a: a.social_tolerance, lambda a: a.final_wealth(), xlabel="tolerance", ylabel="wealth", title="Social Tolerance vs. Wealth")
    plot_relations(agents, lambda a: a.social_tolerance, lambda a: a.social_burnout_sum,  xlabel="tolerance", ylabel="social-burnout", title="Social Tolerance vs. Social Burnout Rate")
    plot_relations(agents, lambda a: a.social_tolerance, lambda a: a.energy_burnout_sum,  xlabel="tolerance", ylabel="energy-burnout",  title="Social Tolerance vs. Energy Burnout Rate")
    plot_relations(agents, lambda a: a.social_burnout_sum, lambda a: a.final_wealth(),  xlabel="social-burnout", ylabel="wealth",  title="Social Burnout Rate vs. Wealth")
