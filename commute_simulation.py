import random
import matplotlib.pyplot as plt
import numpy as np
import logging
import copy 

# Read config.yaml for simulation parameters
import yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

DAY_LENGTH = config['simulation']['day_length']
MAX_TICKS = config['simulation']['max_ticks']
NUM_AGENTS = config['simulation']['num_agents']


# For logging
_TIME = 0 
logger = logging.getLogger(__name__)
logging.basicConfig(filename='simulation.log', encoding='utf-8', filemode='w', level=logging.INFO)


def get_building_coords(building : str):
    # TODO: Right now every agent shares the same house and workplace coordinates
    return config['locations'][building]
    
def _get_crowd_cost(tolerance, crowd=None):
    if crowd is None:
        crowd = int( random.random() * 10 )
        logger.warning(f"Crowd level not provided. Randomly chosen crowd level: {crowd}")

    return -(float(crowd ** 2)/float(tolerance+1e-12)) # 1e-12 to avoid division by zero
    

class Agent:
    def __init__(self, name, social_tolerance, home="home_0", workplace="workplace_0"):
        self.name = name
        self.home = home
        self.workplace = workplace

        self.where = home
        self.state = "idle"
        self.bus_waiting = False
        self.in_recovery = False
        self.recovery_timer = 0

        self.NEED_CATEGORIES = {
        "energy": {"category": "physical", "max": 10, "decay":0.9},
        "alone_time": {"category": "psychological", "max": 10, "decay":1}, # no decay
        "socialization": {"category": "psychological", "max": 10, "decay":1}, # there's no "social" need, but here we lump friendship, family, intimacy
        "wealth": {"category": "economic", "max": None, "decay":1},  # no max cap, no decay
        "self_esteem": {"category": "psychological", "max": 10, "decay":1}, # normally it belongs to "esteem" category, not social  
        }

        self.CATEGORY_IMPORTANCE = { # Equally important atm
            "physical": 1.0,
            "psychological": 1.0,
            "economic": 1.0
        }

        self.initial_needs = self.get_needs_dict(set_zero=False) # Init to max energy
        self.needs =  copy.deepcopy(self.initial_needs)

        self.social_tolerance = social_tolerance
        self.burnout_state = None

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
            needs_dict["energy"] = -1
            needs_dict["wealth"] = -0.01
        
        elif action == "walk":
            if "length" not in kwargs.keys(): 
                len = random.randint(1, 20) # This should be updated if you want to introduce other locations, e.g. a park to rest or actual bus stops
                logger.warning(f"No length is provided! Estimated length (RANDOM) {len}.") 
            else:
                len = kwargs["length"]
        
            needs_dict["energy"] = -len * 0.1
            needs_dict["alone_time"] = +1 
        
        elif action == "rest":
            needs_dict["energy"] = +2
            needs_dict["alone_time"] = +1

        elif action == "sleep":
            needs_dict["energy"] = +5
            needs_dict["alone_time"] = +5

        elif action == "work":
            social_factor =  +1 if random.random() < 0.5 else 0 # Potentially socialize during work

            needs_dict["energy"] = -2
            needs_dict["alone_time"] = -social_factor
            needs_dict["socialization"] = social_factor
            needs_dict["wealth"]  = +5
        
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
            if time % DAY_LENGTH < 20:
                return {"sleep", "rest"}
            elif time % DAY_LENGTH < 60: # TODO: how to define fixed and flexible work hours?
                return {"sleep", "rest", "walk", "take_bus"}
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
            else:
                logger.warning(f"Unknown policy {policy}")
                return {"sleep", "walk", "take_bus"}
        
        # Workplace actions based on policy
        elif self.where == self.workplace:
            if policy == "fixed":
                return self.get_fixed_policy_actions(time, "work")
            else:
                logger.warning(f"Unknown policy {policy}")
                return {"rest", "sleep", "walk", "take_bus", "work"}
            
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
            self._recover_burnout_step()
            return
        
        if self._check_burnout(): # Enters recovery if needed
            return
       
        chosen_action = self.choose_action(time)
        effect = self.get_action_effect(chosen_action) # WARNING: choose_action() also calls this as estimated_effects, here we call it again because actions may have random effects
        # self.apply_action(chosen_action, effect=effect)

        """# POLICY: Fixed schedule -> Shouldn't be here, deliberation is done via needs-satisfaction
        if time % DAY_LENGTH < 20:
            self.move_to(self.workplace)
        elif time % DAY_LENGTH < 60:
            self.do_work()
        elif time % DAY_LENGTH < 80:
            self.move_to(self.home)
        else:
            self.rest()
        # TODO: remove above and call get_available_Actions() - in which when you can work will be stated there -
        # together with needs, we will call eqn.3 """
        
    def _get_distance(self, start, end, type="manhattan"): 
        # TODO: should be A* with city grid, right now it assumes every cell is available and only computes manhattan dist
        if type == "manhattan":
            assert len(start) == 2 and len(end) == 2, f"Expected 2D coordinates, got start: {start} and end: {end}."
            return np.abs(start[0] - end[0]) + np.abs(start[1] - end[1])

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

    def do_work(self):
        if self.where == self.workplace:
            delta =  self.get_action_effect("work")
            self.apply_action("work", delta)
        else:
            logger.warning(f"Agent can only work at {self.workplace}! Currently at {self.where}.")
       
    def rest(self):
        if self.where == self.home:
            self.apply_action("rest",  self.get_action_effect("rest"))
        else:
            logger.warning(f"Agent can only rest at {self.home}! Currently at {self.where}.")

    def apply_action(self, action, effect):
        logger.info(f'[{_TIME}] Agent {self.name} takes action: {action} with effects {effect}.')

        assert len(effect) == len(self.needs), f"Please provide an array of effects with the same length of needs. Provided effect has length {len(effect)}, expected length {len(self.needs)}."
        for key in self.needs.keys():
            self.needs[key] += effect[key]

        # Check for burnout before clamping needs
        if self._check_burnout():
            return

        self._clamp_needs()

    def final_wealth(self):
        return self.needs["wealth"]
    
    def report(self):
        print(f"{self.name} final wealth: {self.final_wealth()}")
        # TODO: More attributes to report?

if __name__ == "__main__":
    # Setup agents
    agents = [Agent("A"+str(i), social_tolerance=random.choice([1, 2, 3, 4, 5, 6 , 7])) for i in range(NUM_AGENTS)]

    # Simulate
    for t in range(MAX_TICKS):
        for agent in agents:
            _TIME = t # For logging
            agent.deliberate_action(t)

    # Gather data for plotting
    tolerance_groups = {}
    for agent in agents:
        tol = agent.social_tolerance
        if tol not in tolerance_groups:
            tolerance_groups[tol] = []
        tolerance_groups[tol].append(agent.final_wealth())

    # TODO: Confidence interval should be computed for trials of same experimental settings 
    # I think for social tolerance levels we should just show max/mean/min values
    # Compute mean and 95% confidence intervals
    labels = sorted(tolerance_groups.keys())
    means = [np.mean(tolerance_groups[t]) for t in labels]
    stds = [np.std(tolerance_groups[t]) for t in labels]
    cis = [1.96 * std / np.sqrt(len(tolerance_groups[t])) for t, std in zip(labels, stds)]

    # Plot
    plt.figure(figsize=(8, 5))
    plt.errorbar(labels, means, yerr=cis, fmt='o', capsize=5, label="95% CI")
    plt.xlabel("Social Tolerance")
    plt.ylabel("Final Wealth")
    plt.title("Final Wealth by Social Tolerance with 95% Confidence Interval")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
