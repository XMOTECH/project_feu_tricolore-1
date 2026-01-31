import turtle

class InterfaceManager:
    def __init__(self):
        self.buttons = []
        
    def draw_controls(self):
        """Dessine une zone de contrôle simple."""
        pen = turtle.Turtle()
        pen.hideturtle()
        pen.penup()
        pen.goto(-380, 250)
        pen.color("white")
        pen.write("Contrôles: [ESPACE=Pause] [S=Start]", font=("Arial", 12, "bold"))