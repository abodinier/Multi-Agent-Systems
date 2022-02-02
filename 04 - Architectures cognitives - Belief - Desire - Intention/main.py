import math
import random
from typing import List

import agentspeak
import agentspeak.runtime
import agentspeak.stdlib
from agentspeak import Literal

import os

actions = agentspeak.Actions(agentspeak.stdlib.actions)

N_RESOURCES = 10  # Nombre de régions


@actions.add_function('.ucb', (float, float, int))
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
        bardane = min(
            self.quantity_bardane,
            random.triangular(0, 1, self.mu_bardane)
        )
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
            self.resources.append(
                Resource(random.random(), random.random(), 15 + 5 * random.random()))
    
    @actions.add(".initialisation_beliefs")  # Initialisation des croyances
    def initialisation_beliefs(self, term, intention):
        for a in agents:
        	for resource_index in range(N_RESOURCES):
            		a.beliefs['values_r', 4].add(Literal('values_r', [resource_index, 0, 0, 0]))
        yield  # doit toujours terminer par yield


    @actions.add(".action_region", 1)
    def action_region(self, term, intention):
        args = term.args[0]

        desired_region = args.evaluate(intention.scope)

        desired_region_resources = self.env.resources[desired_region]
        anis_exploited, bardane_exploited = desired_region_resources.exploit()

        # Fetch croyances
        belief_anis_raw = self.beliefs[('anis', 1)]
        belief_anis = list(belief_anis_raw)[0].args[0]
        belief_bardane_raw = self.beliefs[('bardane', 1)]
        belief_bardane = list(belief_bardane_raw)[0].args[0]

        belief_anis_new, belief_bardane_new = anis_exploited + belief_anis, bardane_exploited + belief_bardane
        anis_literal, bardane_litteral = Literal('anis', [belief_anis_new]), Literal('bardane', [belief_bardane_new])

        self.beliefs[('anis', 1)] = {anis_literal}
        self.beliefs[('bardane', 1)] = {bardane_litteral}

        yield


env = ResourceEnvironment()

global agents

def sans_messages():
    global agents
    with open(os.path.join(os.path.dirname(__file__), "agent_sans_message.asl")) as source:
        agents = env.build_agents(source, 5, actions)

def avec_messages():
    global agents
    with open(os.path.join(os.path.dirname(__file__), "agent_avec_message.asl")) as source:
        agents = env.build_agents(source, 5, actions)

def avec_messages_et_menteur():
    global agents
    with open(os.path.join(os.path.dirname(__file__), "agent_avec_message.asl")) as source:
        agents = env.build_agents(source, 4, actions)
    
    with open(os.path.join(os.path.dirname(__file__), "agent_menteur.asl")) as source:
        agents += env.build_agents(source, 1, actions)

if __name__ == "__main__":
    import sys
    
    mode = sys.argv[1]
    eval(mode)()
    
    random.seed(0)
    env.run()
