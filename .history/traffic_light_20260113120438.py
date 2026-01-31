import turtle

class TrafficLight:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = "ROUGE"
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.penup()
        
    def draw_housing(self):
        """Dessine le boîtier du feu."""
        pass # À implémenter

    def change_state(self, new_state):
        self.state = new_state
        print(f"Feu passé à {self.state}")

    def update(self):
        """Gère le timer interne du feu."""
        pass