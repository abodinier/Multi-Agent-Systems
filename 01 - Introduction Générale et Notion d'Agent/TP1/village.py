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
from mesa.visualization.ModularVisualization import ModularServer, VisualizationElement
from mesa.visualization.modules import ChartModule

class ContinuousCanvas(VisualizationElement):
    local_includes = [
        "./js/simple_continuous_canvas.js",
    ]

    def __init__(self, canvas_height=500,
                 canvas_width=500, instantiate=True):
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
    def  __init__(self,  n_villagers):
        mesa.Model.__init__(self)
        self.space = mesa.space.ContinuousSpace(600, 600, False)
        self.schedule = RandomActivation(self)
        for  _  in  range(n_villagers):
            self.schedule.add(Villager(random.random()  *  600,  random.random()  *  600,  10, random.randint(1,  600), self))
    def step(self):
        self.schedule.step()
        if self.schedule.steps >= 1000:
            self.running = False

class Villager(mesa.Agent):
    def __init__(self, x, y, speed, unique_id: int, model: Village, distance_attack=40, p_attack=0.6):
        super().__init__(unique_id, model)
        self.pos = (x, y)
        self.speed = speed
        self.model = model
        self.distance_attack = distance_attack
        self.p_attack = p_attack

    def portrayal_method(self):
        color = "red"
        r = 3
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": color,
                     "r": r}
        return portrayal

    def step(self):
        self.pos = wander(self.pos[0], self.pos[1], self.speed, self.model)

if  __name__  ==  "__main__":
    server  =  ModularServer(Village, [ContinuousCanvas()],"Village",{"n_villagers":  20})
    server.port = 8521
    server.launch()