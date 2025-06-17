import random
import matplotlib.pyplot as plt
import numpy as np
import logging

# Constants
MAX_TICKS = 500
DAY_LENGTH = 100

# Need indices: [Energy, Social, Wealth]
ENERGY = 0
SOCIAL_ENERGY = 1
WEALTH = 2

# For logging
_TIME = 0 
logger = logging.getLogger(__name__)
logging.basicConfig(filename='simulation.log', encoding='utf-8', filemode='w', level=logging.INFO)

# Action effect matrix (Need-Satisfaction Matrix)
ACTION_EFFECTS = {
    "work": [-2, lambda: -1 if random.random() < 0.5 else 0, 5],
    "rest": [3, 0, 0],
    "socialize": [0, 3, 0],
    "walk": [-1, 0, 0],
    "take_bus": [-1, lambda crowd, tolerance: -(float(crowd)/float(tolerance+1e-12)), 0],  # 1e-12 to avoid division by zero
}

class Agent:
    def __init__(self, name, social_tolerance):
        self.name = name
        self.location = "home"
        self.state = "idle"
        self.bus_waiting = False
        self.in_recovery = False
        self.recovery_timer = 0
        self.needs = [10, 10, 0]  # Initial needs: [Energy, Social, Wealth]
        self.social_tolerance = social_tolerance

        self.burnout_state = None

    def _check_burnout(self):
        # If low social energy, enter recovery
        if self.needs[SOCIAL_ENERGY] <= 0:
            self.in_recovery = True
            self.recovery_timer = 5

            logger.info(f'[{_TIME}][BURNOUT] Agent {self.name} has social burnout.')
            self.burnout_state = "social"
            return True
        
        if self.needs[ENERGY] < 0: # Currently it is the same as social burnout
            self.in_recovery = True
            self.recovery_timer = 5

            logger.info(f'[{_TIME}][BURNOUT] Agent {self.name} has energy burnout.')
            self.burnout_state = "energy"
            return True

        return False

    def _recover_burnout_step(self):
        if self.burnout_state == "social":
            self.needs[SOCIAL_ENERGY] += 0.1 * (self.social_tolerance + 0.1) # +epsilon to avoid multiply by zero, 0.1 results in linear increase in wealth outcome, larger values make them almost equal, this is tuned to make the impact of social tolerance higher
        elif self.burnout_state == "energy":
            self.needs[ENERGY] += 10 # Larger values make energy burnout easier to recover
        else:
            raise ValueError(f"Unrecognized burnout state: {self.burnout_state}")

        self.recovery_timer -= 1
        if self.recovery_timer <= 0:
            self.in_recovery = False
            return True # Recovery completed
        return False

    def act(self, time):
        if self.in_recovery:
            self._recover_burnout_step()
            return
        
        if self._check_burnout(): # Enters recovery if needed
            return
       
        # Simulate basic day: commute, work, return
        if time % DAY_LENGTH < 20:
            self.move_to("work")
        elif time % DAY_LENGTH < 60:
            self.do_work()
        elif time % DAY_LENGTH < 80:
            self.move_to("home")
        else:
            self.rest()

    def move_to(self, target):
        if self.location != target:
            if random.random() < 0.5:
                crowd = random.randint(0, 3)
                if crowd <= self.social_tolerance:
                    delta = ACTION_EFFECTS["take_bus"]
                    self.apply_action("take_bus", [delta[0], delta[1](crowd, self.social_tolerance), delta[2]])
                    self.location = target
                else:
                    self.apply_action("walk", ACTION_EFFECTS["walk"])
                    self.location = target
            else:
                self.apply_action("walk", ACTION_EFFECTS["walk"])
                self.location = target

    def do_work(self):
        delta = ACTION_EFFECTS["work"]
        self.apply_action("work", [delta[0], delta[1](), delta[2]])
       
        
    def rest(self):
        self.apply_action("rest", ACTION_EFFECTS["rest"])

    def apply_action(self, action, effect):
        logger.info(f'[{_TIME}] Agent {self.name} takes action: {action} with effects {effect}.')

        assert len(effect) == len(self.needs), f"Please provide an array of effects with the same length of needs. Provided effect has length {len(effect)}, expected length {len(self.needs)}."
        for i in range(len(effect)):
            self.needs[i] += effect[i]

        # Check for burnout
        if self._check_burnout():
            return

        # Clamp needs
        self.needs[ENERGY] = max(0, min(10, self.needs[ENERGY]))
        self.needs[SOCIAL_ENERGY] = max(0, min(10, self.needs[SOCIAL_ENERGY]))

    def final_wealth(self):
        return self.needs[WEALTH]
    
    def report(self):
        print(f"{self.name} final wealth: {self.final_wealth()}")
        # TODO: More attributes to report?

if __name__ == "__main__":
    # Setup agents
    NUM_AGENTS = 50
    agents = [Agent("A"+str(i), social_tolerance=random.choice([0, 1, 2, 3, 4, 5, 6 , 7])) for i in range(NUM_AGENTS)]

    # Simulate
    for t in range(MAX_TICKS):
        for agent in agents:
            _TIME = t # For logging
            agent.act(t)

    # Gather data for plotting
    tolerance_groups = {}
    for agent in agents:
        tol = agent.social_tolerance
        if tol not in tolerance_groups:
            tolerance_groups[tol] = []
        tolerance_groups[tol].append(agent.final_wealth())

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
