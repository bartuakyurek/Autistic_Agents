import random

# Constants
MAX_TICKS = 500
DAY_LENGTH = 100

# Need indices: [Energy, Social, Wealth]
ENERGY = 0
SOCIAL = 1
WEALTH = 2

# Action effect matrix (Need-Satisfaction Matrix)
ACTION_EFFECTS = {
    "work": [-2, lambda: -1 if random.random() < 0.5 else 0, 5],
    "rest": [3, 0, 0],
    "socialize": [0, 3, 0],
    "walk": [-1, 0, 0],
    "take_bus": [-1, lambda crowd: -crowd, 0],  # crowd is observed when bus arrives
}

class Agent:
    def __init__(self, name):
        self.name = name
        self.location = "home"
        self.state = "idle"
        self.bus_waiting = False
        self.in_recovery = False
        self.recovery_timer = 0
        self.needs = [10, 10, 0]  # Initial needs: [Energy, Social, Wealth]

    def act(self, time, bus_crowd=None):
        if self.in_recovery:
            self.recovery_timer -= 1
            if self.recovery_timer <= 0:
                self.in_recovery = False
                print(f"[{time}] {self.name} recovers social energy.")
            return

        # If low social energy, enter recovery
        if self.needs[SOCIAL] <= 0:
            self.in_recovery = True
            self.recovery_timer = 5
            return

        # Simulate basic day: commute, work, return
        if time % DAY_LENGTH < 20:
            self.move_to("work", time)
        elif time % DAY_LENGTH < 60:
            self.do_work(time)
        elif time % DAY_LENGTH < 80:
            self.move_to("home", time)
        else:
            self.rest(time)

    def move_to(self, target, time):
        if self.location != target:
            # Try to take bus if far; assume bus arrives with 50% chance
            if random.random() < 0.5:
                crowd = random.randint(0, 3)
                if crowd <= self.needs[SOCIAL]:
                    delta = ACTION_EFFECTS["take_bus"]
                    self.apply_action("take_bus", [delta[0], delta[1](crowd), delta[2]], time)
                    self.location = target
                    print(f"[{time}] {self.name} takes bus to {target} (crowd={crowd}).")
                else:
                    self.apply_action("walk", ACTION_EFFECTS["walk"], time)
                    self.location = target
                    print(f"[{time}] {self.name} walks to {target} due to crowd.")
            else:
                self.apply_action("walk", ACTION_EFFECTS["walk"], time)
                self.location = target
                print(f"[{time}] {self.name} walks to {target} (no bus).")

    def do_work(self, time):
        delta = ACTION_EFFECTS["work"]
        self.apply_action("work", [delta[0], delta[1](), delta[2]], time)
        print(f"[{time}] {self.name} works.")

    def rest(self, time):
        self.apply_action("rest", ACTION_EFFECTS["rest"], time)
        print(f"[{time}] {self.name} rests.")

    def apply_action(self, action, effect, time):
        for i in range(3):
            self.needs[i] += effect[i]
        # Clamp needs
        self.needs[ENERGY] = max(0, min(10, self.needs[ENERGY]))
        self.needs[SOCIAL] = max(0, min(10, self.needs[SOCIAL]))

    def report(self):
        print(f"{self.name} final wealth: {self.needs[WEALTH]}")


if __name__ == '__main__':
    # Simulation
    NUM_AGENTS = 10
    agents = [Agent("A"+str(i)) for i in range(NUM_AGENTS)]

    for t in range(MAX_TICKS):
        print(f"\n--- Time {t} ---")
        for agent in agents:
            agent.act(t)

    print("\nSimulation complete. Final reports:")
    for agent in agents:
        agent.report()
