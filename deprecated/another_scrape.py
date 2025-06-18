

# Re-running the code after the execution environment reset

# Re-defining need categories, action effects, and importance levels

NEED_CATEGORIES = {
    "energy": {"category": "physical", "max": 10, "decay":0.9},
    "alone-time": {"category": "psychological", "max": 10, "decay":1}, # no decay
    "socialization": {"category": "psychological", "max": 10, "decay":1}, # there's no "social" need, but here we lump friendship, family, intimacy
    "wealth": {"category": "economic", "max": None, "decay":1},  # no max cap, no decay
    "self-esteem": {"category": "psychological", "max": 10, "decay":1}, # normally it belongs to "esteem" category, not social  

}

CATEGORY_IMPORTANCE = { # Equally important atm
    "physical": 1.0,
    "psychological": 1.0,
    "economic": 1.0
}

# To remove a need from simulation, set all its action-effects to zero
ACTION_EFFECTS = {
    "sleep": {"energy": +5, "alone-time": +5, "socialization": 0, "wealth": 0, "self-esteem":0},
    "work": {"energy": -4, "alone-time": -0.5,  "socialization": +0.5, "wealth": +5, "self-esteem":0}, # TODO: social effects can be random
    "rest": {"energy": +2, "alone-time": +1, "socialization": 0, "wealth": 0, "self-esteem":0},
    "take_bus": {"energy": -1, "alone-time": -1, "socialization": +0.1, "wealth": -0.05, "self-esteem":0}, # TODO: socialization effect can be random
    "walk": {"energy": -2, "alone-time": +1, "socialization": 0, "wealth": 0, "self-esteem":0}
    # TODO: add action meltdown, that lowers esteem
}




class Agent:
    def __init__(self):
        self.needs = {
            key: NEED_CATEGORIES[key]["max"] if NEED_CATEGORIES[key]["max"] is not None else 0
            for key in NEED_CATEGORIES
        }
        self.alpha = 1. # Scales need satisfaction level (for Eqn.4)

    def compute_urgency(self, need_key):
        max_val = NEED_CATEGORIES[need_key]["max"]
        if max_val is None:
            return 0.1  # Minimal urgency for unbounded needs (do not set to 0)
        current_val = self.needs[need_key]
        return 1 - current_val / max_val

    def apply_action(self, action_name):
        # Need-Satisfaction Level update (Eqn. 4)
        effect = ACTION_EFFECTS[action_name]
        for need_key, delta in effect.items():
            self.needs[need_key] += self.alpha * delta 
            
            # Clip need level [0, max]
            max_val = NEED_CATEGORIES[need_key]["max"]
            if max_val is not None:
                clipped_sat = min(max(self.needs[need_key], 0), max_val)
                self.needs[need_key] = clipped_sat

    def timestep_NSL(self):
        # Need-Satisfaction Level decay, NSL_t (Eqn.1)
        for n in self.needs:
            self.needs[n] = NEED_CATEGORIES[n]['decay'] * self.needs[n] # iterative

    def choose_action(self):
        # Deliberation of a_t (Eqn. 3)
        best_score = float('-inf')
        best_action = None

        for action, effects in ACTION_EFFECTS.items():
            score = 0
            for need_key, delta in effects.items():
                category = NEED_CATEGORIES[need_key]["category"]
                importance = CATEGORY_IMPORTANCE.get(category, 1.0)
                urgency = self.compute_urgency(need_key)
                score += delta * urgency * importance 
            if score > best_score:
                best_score = score
                best_action = action

        return best_action


if __name__ == "__main__":
    # Setup agents
    NUM_AGENTS = 5
    agents = [Agent() for i in range(NUM_AGENTS)]

    # Simulate
    for t in range(10):
        for agent in agents:
            _TIME = t # For logging
            chosen_action = agent.choose_action()
            agent.apply_action(chosen_action)
        
            print(chosen_action, agent.needs)
            agent.timestep_NSL() # Water tank model, decay needs
            print(agent.needs)


"""
# Update simulation to support multiple work policies and measure agent outcomes

from enum import Enum
import random
from dataclasses import dataclass, field
from typing import Tuple, Dict

# Define WorkPolicy
class WorkPolicy(Enum):
    FREE = "free"
    FIXED = "fixed"
    FLEXIBLE = "flexible"

@dataclass
class Workplace:
    location: Tuple[int, int]
    policy: WorkPolicy
    work_hours: Tuple[int, int] = (30, 40)  # default window

@dataclass
class NeedSatisfaction:
    # Need-Satisfaction matrix per action
    matrix: Dict[str, Dict[str, float]]

    def apply(self, needs: Dict[str, float], action: str, modifier: float = 1.0) -> Dict[str, float]:
        if action not in self.matrix:
            return needs
        return {
            need: needs.get(need, 0) + self.matrix[action].get(need, 0) * modifier
            for need in needs
        }

@dataclass
class Agent:
    id: int
    home: Tuple[int, int]
    work: Workplace
    location: Tuple[int, int]
    needs: Dict[str, float]
    social_energy_threshold: float
    time: int = 0
    total_wealth: float = 0
    resting: bool = False

    def decide_next_action(self) -> str:
        if self.resting:
            if self.needs["social_energy"] >= self.social_energy_threshold:
                self.resting = False
            else:
                return "rest"

        if self.location == self.work.location:
            if can_work_now(self, self.work, self.time):
                return "work"
            else:
                return "wait"

        if self.location == self.home:
            return "walk_to_work"
        if self.location == self.work.location:
            return "walk_to_home"
        return "walk"

    def update_state(self, action: str, nsm: NeedSatisfaction):
        modifier = 1.0
        if action == "work":
            modifier = work_satisfaction_modifier(self.work, self.time)
            if random.random() < 0.2:  # probability to reduce social energy
                self.needs["social_energy"] -= 2

        self.needs = nsm.apply(self.needs, action, modifier)

        if self.needs["social_energy"] <= 0:
            self.resting = True

        if action == "work":
            self.total_wealth += nsm.matrix[action].get("wealth", 0) * modifier

        self.time += 1

# Helper functions
def can_work_now(agent: Agent, workplace: Workplace, current_time: int) -> bool:
    start, end = workplace.work_hours
    if workplace.policy == WorkPolicy.FREE:
        return True
    elif workplace.policy == WorkPolicy.FIXED:
        return start <= current_time <= end
    elif workplace.policy == WorkPolicy.FLEXIBLE:
        return (start - 5) <= current_time <= (end + 5)
    return False

def work_satisfaction_modifier(workplace: Workplace, time: int) -> float:
    if workplace.policy == WorkPolicy.FREE:
        return 1.0
    center = (workplace.work_hours[0] + workplace.work_hours[1]) / 2
    diff = abs(center - time)
    max_diff = 10
    return max(0, 1 - (diff / max_diff))

# Example simulation run
def run_simulation(work_policy: WorkPolicy, steps: int = 100, num_agents: int = 5):
    # Define shared workplace
    workplace = Workplace(location=(5, 5), policy=work_policy)

    # Define NSM
    NSM = NeedSatisfaction(matrix={
        "work": {"wealth": 10, "energy": -5, "social_energy": -1},
        "walk": {"energy": -1},
        "rest": {"social_energy": 2},
        "wait": {"energy": -0.5}
    })

    # Initialize agents
    agents = [
        Agent(id=i,
              home=(0, 0),
              work=workplace,
              location=(0, 0),
              needs={"energy": 100, "social_energy": 20, "wealth": 0},
              social_energy_threshold=5)
        for i in range(num_agents)
    ]

    for _ in range(steps):
        for agent in agents:
            action = agent.decide_next_action()
            if action == "walk_to_work":
                agent.location = workplace.location
                action = "walk"
            elif action == "walk_to_home":
                agent.location = agent.home
                action = "walk"

            agent.update_state(action, NSM)

    return [agent.total_wealth for agent in agents]

# Run three experiments with different work policies
results = {
    "free": run_simulation(WorkPolicy.FREE),
    "fixed": run_simulation(WorkPolicy.FIXED),
    "flexible": run_simulation(WorkPolicy.FLEXIBLE),
}
print(results)

"""