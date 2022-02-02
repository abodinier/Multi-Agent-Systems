import math
import random
from typing import List

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib

import os

actions = agentspeak.Actions(agentspeak.stdlib.actions)

N_RESOURCES = 2


def ucb(mu, ni, n):
    if n == 0:
        return 200
    elif ni == 0:
        return 200
    else:
        return mu/n + math.log(2*n/ni)


class Resource:
    def __init__(self, mu_anis, mu_bardane, quantity):
        self.mu_anis = mu_anis
        self.mu_bardane = mu_bardane
        self.quantity_anis = quantity
        self.quantity_bardane = quantity

    def exploit(self):
        anis = min(self.quantity_anis, random.triangular(0, 1, self.mu_anis))
        bardane = min(self.quantity_bardane, random.triangular(0, 1, self.mu_bardane))
        self.quantity_anis = self.quantity_anis - anis
        self.quantity_bardane = self.quantity_bardane - bardane
        return anis, bardane

    def __str__(self):
        return str(self.__dict__)


class ResourceEnvironment(agentspeak.runtime.Environment):
    resources: List[Resource]

    def __init__(self):
        super().__init__()
        self.resources = []
        for i in range(N_RESOURCES):
            self.resources.append(Resource(random.random(), random.random(), 15 + 5 * random.random()))

env = ResourceEnvironment()

with open(os.path.join(os.path.dirname(__file__), "agent.asl")) as source:
    agents = env.build_agents(source, 5, actions)

if __name__ == "__main__":
    random.seed(0)
    env.run()