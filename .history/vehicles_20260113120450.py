import turtle
import random

class Vehicle:
    def __init__(self, id_veh, spawn_x, spawn_y):
        self.id = id_veh
        self.x = spawn_x
        self.y = spawn_y
        self.speed = 2
        
        # Création de la forme Turtle
        self.shape = turtle.Turtle()
        self.shape.shape("square")
        self.shape.shapesize(stretch_wid=1, stretch_len=2) # Forme rectangle
        self.shape.penup()
        self.shape.goto(self.x, self.y)
    
    def move(self):
        self.x += self.speed
        self.shape.setx(self.x)

class VehicleManager:
    def __init__(self):
        self.vehicles = []

    def spawn_vehicle(self):
        """Crée une nouvelle voiture."""
        pass

    def update_vehicles(self):
        """Fait bouger toutes les voitures."""
        for v in self.vehicles:
            v.move()