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
EPS = 1e-5


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
        
        # Usefull state variables
        self.max_speed = speed
        self.is_in_quicksand = False
        self.demining_in_progress = False
        self.avoiding_collision = False
        self.in_danger = False
        self.following_indication = False
        self.ignore_steps_count = 0
    
    def get_distance_from(self, o2, o1=None):
        """Return the distance between agent and object 2

        Args:
            o2 (Object): Object that must have two attributes : x and y
            o1 (Tuple): (x, y) when we want to compute the distance between o2 and o1 which is not the agent's position
        """
        if o1:
            return ( (o1[0] - o2.x)**2 + (o1[1] - o2.y)**2 ) ** .5
        return ( (self.x - o2.x)**2 + (self.y - o2.y)**2 ) ** .5
    
    def mark_danger(self):
        """Leave a danger marker
        """
        marker = Marker(self.x, self.y, MarkerPurpose.DANGER)
        self.model.markers.append(marker)
        self.ignore_steps_count = self.speed / 2
    
    def mark_indication(self, direction):
        """Leave an indication marer

        Args:
            direction (float): Angle in radians
        """
        marker = Marker(self.x, self.y, MarkerPurpose.INDICATION, direction=direction)
        self.model.markers.append(marker)
        self.ignore_steps_count = self.speed / 2
    
    def check_quicksands(self):
        """Checks if the robot is in quicksand and leave a marker if it just leaved a quicksand

        Returns:
            None: Returns None
        """
        old_is_in_quicksand = self.is_in_quicksand
        
        for quicksand in self.model.quicksands:
            if self.get_distance_from(quicksand) <= quicksand.r:
                self.speed = self.max_speed / 2
                self.is_in_quicksand = True
                self.model.in_quicksands += 1
                return None
        
        self.is_in_quicksand = False
        self.speed = self.max_speed
        
        if old_is_in_quicksand == True and self.is_in_quicksand == False:
            self.mark_danger()

    def compute_trajectory(self):
        """Return the new position if the robots move with its current direction and speed, but it does not updates the position

        Returns:
            tuple: (new_x, new_y)
        """
        new_x = max(min(self.x + math.cos(self.angle) * self.speed, self.model.space.x_max), self.model.space.x_min)
        new_y = max(min(self.y + math.sin(self.angle) * self.speed, self.model.space.y_max), self.model.space.y_min)
        
        return new_x, new_y
    
    def check_collision_agent(self, new_x, new_y):
        """Checks if with the potential new position there will be a collision with other agents

        Args:
            new_x (float): New x 
            new_y (float): New y

        Returns:
            bool: If there is at least one collision, returns True, otherwise, False
        """
        for agent in self.model.schedule.agents:
            if agent.unique_id != self.unique_id:
                if self.get_distance_from(agent) < self.sight_distance:
                    AV = np.array([agent.x - self.x, agent.y - self.y])  # vecteur agent -> voisin
                    u = np.array([new_x - self.x, new_y - self.y])  # agent_ancienne_pos -> agent_nouvelle_pos
                    u = u / (u @ u.T + EPS) ** .5  # normalize u
                    AH = AV @ u  # orthogonal projection of AV over u

                    HV = (AV @ AV - AH ** 2) ** .5  # Pythagore
                    if HV <= agent.speed:
                        return True

        return False
    
    def check_collision_obstacles(self, new_x, new_y):
        """Checks if with the potential new position there will be a collision with obstacles

        Args:
            new_x (float): new x 
            new_y (float): new y

        Returns:
            bool: True if collision, otherwise False
        """
        for obstacle in self.model.obstacles:
            if self.get_distance_from(obstacle) < self.sight_distance:
                dist = self.get_distance_from(obstacle, (new_x, new_y))
                if dist <= obstacle.r:
                    return True
        
        return False
    
    def check_collision_borders(self, new_x, new_y):
        """Checks if with the potential new position there will be a collision with borders

        Args:
            new_x (float): new x 
            new_y (float): new y

        Returns:
            bool: True if collision, otherwise False
        """
        if self.model.space.x_min <= new_x <= self.model.space.x_max:
            if self.model.space.y_min <= new_y <= self.model.space.y_max:
                return False
        return True

    def check_collision(self):
        new_pos = self.compute_trajectory()
        return self.check_collision_agent(*new_pos) or self.check_collision_obstacles(*new_pos) or self.check_collision_borders(*new_pos)
    
    def get_markers(self):
        """Returns the list of all markers at sight with the distance to them

        Returns:
            tuple: a tuple of list of tuples : (dangers, indications) with danger in the form [(danger_1, 53), ...]
        """
        dangers, indications = [], []
        
        for marker in self.model.markers:
            
            dist = self.get_distance_from(marker)
            
            if dist < self.sight_distance:
                
                if marker.purpose == MarkerPurpose.DANGER:
                    dangers.append(
                        (marker, dist)
                    )
                
                if marker.purpose == MarkerPurpose.INDICATION:
                    indications.append(
                        (marker, dist)
                    )
                
        return dangers, indications
    
    def check_markers(self):
        """Pick marker and update angle accordingly (priority to danger markers)
        """
        dangers, indications = self.get_markers()
        
        if dangers:
            danger = min(dangers, key=lambda x: x[1])[0]
            
            self.in_danger = True
            (self.x, self.y), self.angle = go_to(
                self.x, self.y, self.speed, danger.x, danger.y
            )
            
            if self.get_distance_from(danger) < EPS:
                self.model.markers.remove(danger)
                self.angle = - self.angle
                self.in_danger = False
                self.x, self.y = self.compute_trajectory()

        if indications:
            indication = min(indications, key=lambda x: x[1])[0]
            
            self.following_indication = True
            
            (self.x, self.y), self.angle = go_to(
                self.x, self.y, self.speed, indication.x, indication.y
            )
            
            if self.get_distance_from(indication) < EPS:
                self.model.markers.remove(indication)
                self.angle = (self.angle + math.pi) % (2*math.pi)
                self.following_indication = False
                self.x, self.y = self.compute_trajectory()
    
    def demining(self):
        """The demining set of actions (look for mine, go to mine, destroy and leave marker)
        """
        mines = []
        for mine in self.model.mines:
            dist = self.get_distance_from(mine)
            if dist < self.sight_distance:
                mines.append(
                    (mine, dist)
                )
        
        if mines:
            mine, dist = min(mines, key=lambda x: x[1])
        
            self.demining_in_progress = True
            
            (self.x, self.y), self.angle = go_to(
                    self.x, self.y, self.speed, mine.x, mine.y
            )
            
            if self.get_distance_from(mine) < EPS:
                self.model.mines.remove(mine)
                self.model.mine_counter += 1
                self.mark_indication(direction=self.angle)
                self.demining_in_progress = False

    def wander(self):
        new_x, new_y = self.compute_trajectory()  # Move
        self.x = new_x
        self.y = new_y
        if self.proba_chgt_angle <= np.random.uniform(0, 1):
            self.angle = np.random.uniform(0, 2*np.pi)

    def step(self):
        # Check the quicksands
        self.check_quicksands()
        
        # Check collision which is the No 1 danger
        c = 0
        stop = False
        while(self.check_collision()):
            self.angle = np.random.uniform(0, 2*np.pi)
            self.avoiding_collision = True
            c += 1
            if c > 10:
                stop = True  # We did not found a way to avoid collision, so we let the other agents go
                break
        
        if ~stop:
            
            if self.avoiding_collision:  # We are not escaping from a collision, so we can continue
                self.wander()
                self.avoiding_collision = False
            
            else:
            
                self.demining()

                if not self.demining_in_progress:
                    
                    if self.ignore_steps_count == 0:
                        self.check_markers()

                    if ~self.in_danger and ~self.following_indication:
                        
                        self.wander()
        
        self.speed = self.max_speed
        self.ignore_steps_count = max(0, self.ignore_steps_count - 1)



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
                         "Mine counter": lambda model: model.mine_counter,
                         "In quicksands": lambda model: model.in_quicksands,
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
        self.mine_counter = 0
        self.in_quicksands = 0
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
                          "Color": "Green"},
                         {"Label": "Mine counter",
                          "Color": "black"},
                         {"Label": "In quicksands",
                          "Color": "Blue"}
                         ],
                        data_collector_name='datacollector')
    server = ModularServer(MinedZone,
                           [ContinuousCanvas(),
                            chart],
                           "Deminer robots",
                           {"n_robots": mesa.visualization.
                            ModularVisualization.UserSettableParameter('slider', "Number of robots", 7, 1,
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
