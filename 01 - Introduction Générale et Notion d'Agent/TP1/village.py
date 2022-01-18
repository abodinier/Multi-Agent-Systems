import math
import random
import numpy as np
from collections import defaultdict

import uuid
import mesa
import numpy
import pandas
from mesa import space
from mesa.batchrunner import BatchRunner
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.visualization.ModularVisualization import ModularServer, VisualizationElement, UserSettableParameter
from mesa.visualization.modules import ChartModule

ENTITIES_COLOR = {
    "villager": "blue",
    "lycanthrope": "red",
    "cleric": "green",
    "hunter": "black"
}
ENTITIES_SIZES = {
    "villager": 3,
    "lycanthrope": 6,
    "cleric": 3,
    "hunter": 3
}

CANVAS_HEIGHT = 500
CANVAS_WIDTH = 500
class ContinuousCanvas(VisualizationElement):
    local_includes = [
        "./js/simple_continuous_canvas.js",
    ]

    def __init__(self, canvas_height=CANVAS_HEIGHT, canvas_width=CANVAS_WIDTH, instantiate=True):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.identifier = "space-canvas"
        if (instantiate):
            new_element = ("new Simple_Continuous_Module({}, {},'{}')".
                           format(self.canvas_width, self.canvas_height, self.identifier))
            self.js_code = "elements.push(" + new_element + ");"

    def portrayal_method(self, obj):
        return obj.portrayal_method()

    def render(self, model):
        representation = defaultdict(list)
        for obj in model.schedule.agents:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.pos[0] - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.pos[1] - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        return representation

def wander(x, y, speed, model):
    r = random.random() * math.pi * 2
    new_x = max(min(x + math.cos(r) * speed, model.space.x_max), model.space.x_min)
    new_y = max(min(y + math.sin(r) * speed, model.space.y_max), model.space.y_min)

    return new_x, new_y

class  Village(mesa.Model):
    def  __init__(self,  n_villagers, n_lycanthropes, n_clerics, n_hunters):
        mesa.Model.__init__(self)
        self.space = mesa.space.ContinuousSpace(CANVAS_HEIGHT, CANVAS_WIDTH, False)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector(
            model_reporters = {
                "Population":lambda m: len([a for a in m.schedule.agents]),
                "Humans": lambda m: len([a for a in m.schedule.agents if a.entity != "lycanthrope"]),
                "Lycanthropes": lambda m: len([a for a in m.schedule.agents if a.entity == "lycanthrope"]),
                "Clerics": lambda m: len([a for a in m.schedule.agents if a.entity == "cleric"]),
                "Hunters": lambda m: len([a for a in m.schedule.agents if a.entity == "hunter"])
            }
        )
        
        n_tot = n_villagers + n_lycanthropes + n_clerics + n_hunters
        list_tot = [i for i in range(n_tot)]
        
        lycanthropes_indices = sorted(
            np.random.choice(
                list_tot,
                size=n_lycanthropes,
                replace=False)
        )
        
        cleric_indices = sorted(
            np.random.choice(
                list(set(list_tot) - set(lycanthropes_indices)),
                size=n_clerics,
                replace=False)
        )
        
        hunter_indices = sorted(
            np.random.choice(
                list(set(list_tot) - set(lycanthropes_indices) - set(cleric_indices)),
                size=n_hunters,
                replace=False)
        )
        
        for  i  in  range(n_tot):
            
            is_cleric = i in cleric_indices
            is_lycanthrope = i in lycanthropes_indices
            is_hunter = i in hunter_indices
            
            if is_cleric:
                entity = "cleric"
                self.schedule.add(
                Cleric(
                    x=random.random()  *  600,
                    y=random.random()  *  600,
                    speed=10,
                    unique_id=uuid.uuid1(),
                    model=self,
                    entity=entity
                )
            )
            if is_lycanthrope:
                entity = "lycanthrope"
                self.schedule.add(
                    Villager(
                        x=random.random()  *  600,
                        y=random.random()  *  600,
                        speed=10,
                        unique_id=uuid.uuid1(),
                        model=self,
                        entity=entity
                    )
                )
            if is_hunter:
                entity = "hunter"
                self.schedule.add(
                    Hunter(
                        x=random.random()  *  600,
                        y=random.random()  *  600,
                        speed=10,
                        unique_id=uuid.uuid1(),
                        model=self,
                        entity=entity
                    )
                )
            else:
                entity = "villager"
                self.schedule.add(
                    Villager(
                        x=random.random()  *  600,
                        y=random.random()  *  600,
                        speed=10,
                        unique_id=uuid.uuid1(),
                        model=self,
                        entity=entity
                    )
                )
    
    def step(self):
        self.schedule.step()
        self.datacollector.collect(self)
        if self.schedule.steps >= 1000:
            self.running = False


class Person(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village, entity: str):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model
        self.entity = entity
        self.is_transformed = False

    def portrayal_method(self):
        color = ENTITIES_COLOR[self.entity]
        r = ENTITIES_SIZES[self.entity] if self.is_transformed else 3
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Layer": 1,
            "Color": color,
            "r": r
        }
        return portrayal
    
    def find_neighbors(self, min_distance, entities="all"):
        neighbors = []
        agents = self.model.schedule.agent_buffer()
        
        def distance(pos1, pos2, measure='euclidian', norm=2):
            if measure == 'euclidian':
                dist = 0
                for a, b in zip(pos1, pos2):
                    dist += (a - b) ** norm
                return dist ** (1 / norm)
            else:
                raise Exception(f"measure {measure} not implemented!")
        
        for agent in agents:
            if agent.unique_id != self.unique_id:
                dist = distance(agent.pos, self.pos)
                dist = dist - ENTITIES_SIZES[agent.entity] / 2 - ENTITIES_SIZES[self.entity] / 2
                if dist <= min_distance:
                    if agent.entity in entities or entities == "all":
                        neighbors.append(agent)
        
        return neighbors

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)


class Villager(Person):
    def __init__(self, x, y, speed, unique_id: int, model: Village, entity: str, distance_attack=40, p_attack=0.6, attack_entities=["villager"]):
        super().__init__(x, y, speed, unique_id, model, entity)
        self.distance_attack = distance_attack
        self.p_attack = p_attack
        self.attack_entities = attack_entities
        self.is_transformed = False

    def attack(self):
        if np.random.uniform(0, 1) < self.p_attack:
            within_range = self.find_neighbors(
                min_distance=self.distance_attack,
                entities=self.attack_entities
            )
            if len(within_range) > 0:
                target = random.choice(within_range)
                
                self.model.schedule._agents[target.unique_id].entity = "lycanthrope"

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)
        if self.entity == "lycanthrope":
            if not self.is_transformed and np.random.uniform(0, 1) < 0.1:
                self.is_transformed = True
            if self.is_transformed:
                self.attack()

class Cleric(Person):
    def __init__(self, x, y, speed, unique_id: int, model: Village, entity: str, healing_range=30):
        super().__init__(x, y, speed, unique_id, model, entity)
        self.healing_range = healing_range
    
    def heal(self):
        within_range = self.find_neighbors(min_distance=self.healing_range, entities="lycanthrope")
        for agent in within_range:
            self.model.schedule._agents[agent.unique_id].entity = "villager"
            self.model.schedule._agents[agent.unique_id].is_transformed = False

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)
        self.heal()

class Hunter(Person):
    def __init__(self, x, y, speed, unique_id: int, model: Village, entity: str, attack_range=40):
        super().__init__(x, y, speed, unique_id, model, entity)
        self.attack_range = attack_range
    
    def hunt(self):
        within_range = self.find_neighbors(min_distance=self.attack_range, entities="lycanthrope")
        for agent in within_range:
            if self.model.schedule._agents[agent.unique_id].is_transformed:
                del self.model.schedule._agents[agent.unique_id]
    
    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)
        self.hunt()

chart = ChartModule(
    canvas_height=200,
    canvas_width=CANVAS_WIDTH,
    series = [
        {
            "Label": "Population",
            "Color": "yellow"
        },
        {
            "Label": "Humans",
            "Color": "blue"
        },
        {
            "Label": "Lycanthropes",
            "Color": "red"
        }
    ],
    data_collector_name='datacollector'
)

def run_single_server():
    server  =  ModularServer(
        Village,
        [chart, ContinuousCanvas()],
        name="Village",
        model_params={
            "n_villagers":  UserSettableParameter(param_type='number', name="Villagers", value=20, min_value=0, max_value=100),
            "n_lycanthropes": UserSettableParameter(param_type='number', name="Lycanthropes", value=5, min_value=0, max_value=100),
            "n_clerics": UserSettableParameter(param_type='number', name="Clerics", value=1, min_value=0, max_value=100),
            "n_hunters": UserSettableParameter(param_type='number', name="Hunters", value=2, min_value=0, max_value=100)
        }
    )
    server.port = 8521
    server.launch()

def run_batch():
    batchrunner = BatchRunner(
        model_cls = Village,
        variable_parameters = {
            "n_villagers":  [50],
            "n_lycanthropes": [5],
            "n_clerics": [i for i in range(11)],
            "n_hunters": [1]
        },
        model_reporters = {
                "Population":lambda m: len([a for a in m.schedule.agents]),
                "Humans": lambda m: len([a for a in m.schedule.agents if a.entity != "lycanthrope"]),
                "Lycanthropes": lambda m: len([a for a in m.schedule.agents if a.entity == "lycanthrope"]),
                "Clerics": lambda m: len([a for a in m.schedule.agents if a.entity == "cleric"]),
                "Hunters": lambda m: len([a for a in m.schedule.agents if a.entity == "hunter"])
            }
    )
    batchrunner.run_all()
    df = batchrunner.get_model_vars_dataframe()
    return df

if  __name__  ==  "__main__":
    df = run_batch()
    df.to_csv("./df.csv")