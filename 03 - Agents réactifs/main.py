import enum
import math
import random
import uuid
from enum import Enum

import mesa
import numpy as np
from collections import defaultdict

import mesa.space
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.visualization.ModularVisualization import VisualizationElement, ModularServer
from mesa.visualization.modules import ChartModule

MAX_ITERATION = 100
PROBA_CHGT_ANGLE = 0.01


def move(x, y, speed, angle):
    return x + speed * math.cos(angle), y + speed * math.sin(angle)


def go_to(x, y, speed, dest_x, dest_y):
    if np.linalg.norm((x - dest_x, y - dest_y)) < speed:
        return (dest_x, dest_y), 2 * math.pi * random.random()
    else:
        angle = math.acos((dest_x - x)/np.linalg.norm((x - dest_x, y - dest_y)))
        if dest_y < y:
            angle = - angle
        return move(x, y, speed, angle), angle


class MarkerPurpose(Enum):
    DANGER = enum.auto(),
    INDICATION = enum.auto()


class ContinuousCanvas(VisualizationElement):
    local_includes = [
        "./js/simple_continuous_canvas.js",
    ]

    def __init__(self, canvas_height=500,
                 canvas_width=500, instantiate=True):
        VisualizationElement.__init__(self)
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
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        for obj in model.mines:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        for obj in model.markers:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        for obj in model.obstacles:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        for obj in model.quicksands:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        return representation


class Obstacle:  # Environnement: obstacle infranchissable
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r

    def portrayal_method(self):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": "black",
                     "r": self.r}
        return portrayal


class Quicksand:  # Environnement: ralentissement
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r

    def portrayal_method(self):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": "olive",
                     "r": self.r}
        return portrayal


class Mine:  # Environnement: element a ramasser
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def portrayal_method(self):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 2,
                     "Color": "black",
                     "r": 2}
        return portrayal


class Marker:  # La classe pour les balises
    def __init__(self, x, y, purpose, direction=None):
        self.x = x
        self.y = y
        self.purpose = purpose
        if purpose == MarkerPurpose.INDICATION:
            if direction is not None:
                self.direction = direction
            else:
                raise ValueError("Direction should not be none for indication marker")

    def portrayal_method(self):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 2,
                     "Color": "red" if self.purpose == MarkerPurpose.DANGER else "green",
                     "r": 2}
        return portrayal


class Robot(Agent):  # La classe des agents
    def __init__(self, unique_id, model, x, y, speed, sight_distance, angle=0.0, proba_chgt_angle=.1):
        super().__init__(unique_id, model)
        self.x = x
        self.y = y
        self.speed = speed
        self.sight_distance = sight_distance
        self.angle = angle
        self.counter = 0
        self.proba_chgt_angle = proba_chgt_angle
    
    def get_distance_from(self, o2, o1=None):
        """Return the distance between agent and object 2

        Args:
            o2 (Object): Object that must have two attributes : x and y
            o1 (Tuple): (x, y) when we want to compute the distance between o2 and o1 which is not the agent's position
        """
        if o1:
            return ( (o1[0] - o2.x)**2 + (o1[1] - o2.y)**2 ) ** .5
        return ( (self.x - o2.x)**2 + (self.y - o2.y)**2 ) ** .5
    
    def is_in_quicksand(self):
        for quicksand in self.model.quicksands:
            if self.get_distance_from(quicksand) <= quicksand.r:
                return True
        return False

    def compute_trajectory(self, speed):
        new_x = max(min(self.x + math.cos(self.angle) * speed, self.model.space.x_max), self.model.space.x_min)
        new_y = max(min(self.y + math.sin(self.angle) * speed, self.model.space.y_max), self.model.space.y_min)
        
        return new_x, new_y
    
    def random_change_angle(self):
        if self.proba_chgt_angle < np.random.uniform(0, 1):
            self.angle = np.random.uniform(0, 2*np.pi)
    
    def check_collision_agent(self, new_x, new_y):
        for agent in self.model.schedule.agents:
            if agent.unique_id != self.unique_id:
                if self.get_distance_from(agent) < self.sight_distance:
                    AV = np.array([agent.x - self.x, agent.y - self.y])  # vecteur agent -> voisin
                    
                    u = np.array([new_x - self.x, new_y - self.y])  # agent_ancienne_pos -> agent_nouvelle_pos
                    u /= (u @ u.T) ** .5  # normalize u
                    
                    AH = AV @ u  # orthogonal projection of AV over u

                    HV = (AV @ AV - AH ** 2) ** .5  # Pythagore
                    
                    if HV <= agent.speed:
                        return True
                    
                    return False
    
    def check_collision_obstacles(self, new_x, new_y):
        for obstacle in self.model.obstacles:
            if self.get_distance_from(obstacle) < self.sight_distance:
                dist = self.get_distance_from(obstacle, (new_x, new_y))
                if dist <= obstacle.r:
                    return True
        return False

    def check_collision(self, speed):
        new_pos = self.compute_trajectory(speed)
        return self.check_collision_agent(*new_pos) or self.check_collision_obstacles(*new_pos)
    
    def look_for_mines(self):
        """Return the first mine found (distance < sight_distance)

        Returns:
            Mine or None: The first mine found or None if no mine found
        """
        for mine in self.model.mines:
            if self.get_distance_from(mine) < self.sight_distance:
                return mine
        return None
    
    def go_to_mine(self, speed, mine):
        dist = self.get_distance_from(mine)
        theta = math.asin( (mine.y - self.y) / dist )
        catch = False
        if dist <= speed:
            speed = dist
            catch = True
        return theta, speed, catch
    
    def destroy_mine(self, mine):
        self.model.mines.remove(mine)
    
    def wander(self, speed):
        new_x, new_y = self.compute_trajectory(speed)  # Move
        self.x = new_x
        self.y = new_y

    def step(self):
        speed = self.speed / 2 if self.is_in_quicksand() else self.speed  # Speed is /2 if in quicksand
        mine = self.look_for_mines()
        if mine:
            theta, speed, catch = self.go_to_mine(speed, mine)
            self.angle = theta
            if catch:
                self.wander(speed)  # reach mine
                self.destroy_mine(mine)  # destroy mine
            else:
                if self.check_collision_agent(*self.compute_trajectory(speed)):
                    self.wander(speed=0)  # wait for the agent to move
                while(self.check_collision_obstacles(*self.compute_trajectory(speed))):  # must change trajectory
                    self.angle = np.random.uniform(0, 2*np.pi)
        else:
            self.random_change_angle()  # random angle change
            while self.check_collision(speed):
                self.angle = np.random.uniform(0, 2*np.pi)
        self.wander(speed)

    def portrayal_method(self):
        portrayal = {"Shape": "arrowHead", "s": 1, "Filled": "true", "Color": "Red", "Layer": 3, 'x': self.x,
                     'y': self.y, "angle": self.angle}
        return portrayal


class MinedZone(Model):
    collector = DataCollector(
        model_reporters={"Mines": lambda model: len(model.mines),
                         "Danger markers": lambda model: len([m for m in model.markers if
                                                          m.purpose == MarkerPurpose.DANGER]),
                         "Indication markers": lambda model: len([m for m in model.markers if
                                                          m.purpose == MarkerPurpose.INDICATION]),
                         },
        agent_reporters={})

    def __init__(self, n_robots, n_obstacles, n_quicksand, n_mines, speed):
        Model.__init__(self)
        self.space = mesa.space.ContinuousSpace(600, 600, False)
        self.schedule = RandomActivation(self)
        self.mines = []  # Access list of mines from robot through self.model.mines
        self.markers = []  # Access list of markers from robot through self.model.markers (both read and write)
        self.obstacles = []  # Access list of obstacles from robot through self.model.obstacles
        self.quicksands = []  # Access list of quicksands from robot through self.model.quicksands
        for _ in range(n_obstacles):
            self.obstacles.append(Obstacle(random.random() * 500, random.random() * 500, 10 + 20 * random.random()))
        for _ in range(n_quicksand):
            self.quicksands.append(Quicksand(random.random() * 500, random.random() * 500, 10 + 20 * random.random()))
        for _ in range(n_robots):
            x, y = random.random() * 500, random.random() * 500
            while [o for o in self.obstacles if np.linalg.norm((o.x - x, o.y - y)) < o.r] or \
                    [o for o in self.quicksands if np.linalg.norm((o.x - x, o.y - y)) < o.r]:
                x, y = random.random() * 500, random.random() * 500
            self.schedule.add(
                Robot(int(uuid.uuid1()), self, x, y, speed,
                      2 * speed, random.random() * 2 * math.pi))
        for _ in range(n_mines):
            x, y = random.random() * 500, random.random() * 500
            while [o for o in self.obstacles if np.linalg.norm((o.x - x, o.y - y)) < o.r] or \
                    [o for o in self.quicksands if np.linalg.norm((o.x - x, o.y - y)) < o.r]:
                x, y = random.random() * 500, random.random() * 500
            self.mines.append(Mine(x, y))
        self.datacollector = self.collector

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
        if not self.mines:
            self.running = False


def run_single_server():
    chart = ChartModule([{"Label": "Mines",
                          "Color": "Orange"},
                         {"Label": "Danger markers",
                          "Color": "Red"},
                         {"Label": "Indication markers",
                          "Color": "Green"}
                         ],
                        data_collector_name='datacollector')
    server = ModularServer(MinedZone,
                           [ContinuousCanvas(),
                            chart],
                           "Deminer robots",
                           {"n_robots": mesa.visualization.
                            ModularVisualization.UserSettableParameter('slider', "Number of robots", 7, 3,
                                                                       15, 1),
                            "n_obstacles": mesa.visualization.
                            ModularVisualization.UserSettableParameter('slider', "Number of obstacles", 5, 2, 10, 1),
                            "n_quicksand": mesa.visualization.
                            ModularVisualization.UserSettableParameter('slider', "Number of quicksand", 5, 2, 10, 1),
                            "speed": mesa.visualization.
                            ModularVisualization.UserSettableParameter('slider', "Robot speed", 15, 5, 40, 5),
                            "n_mines": mesa.visualization.
                            ModularVisualization.UserSettableParameter('slider', "Number of mines", 15, 5, 30, 1)})
    server.port = 8521
    server.launch()


if __name__ == "__main__":
    run_single_server()
