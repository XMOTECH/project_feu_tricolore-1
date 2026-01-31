import turtle

class TrafficLight:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.state = "ROUGE"
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.penup()
        self.timer = 0

        # Configuration visuelle
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0)
        self.pen.penup()
        
        # Durées (en frames, approx 50 frames = 1 seconde)
        # Plus tard, ces valeurs viendront du fichier scenarios.py
        self.durations = {"VERT": 100, "ORANGE": 40, "ROUGE": 100}
        
        self.draw_housing()
        self.update_visuals()
        
        
    def draw_housing(self):
        """Dessine le boîtier du feu."""
        self.pen.goto(self.x - 15, self.y + 60)
        self.pen.color("black")
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(30)
            self.pen.right(90)
            self.pen.forward(100)
            self.pen.right(90)
        self.pen.end_fill()

    def update_visuals(self):
        """Allume le bon cercle selon l'état."""
        # Positions des feux: Rouge(haut), Orange(milieu), Vert(bas)
        colors = {"ROUGE": "darkred", "ORANGE": "sienna", "VERT": "darkgreen"}
        
        # On allume la couleur active (les autres restent sombres)
        if self.state == "ROUGE": colors["ROUGE"] = "red"
        elif self.state == "ORANGE": colors["ORANGE"] = "orange"
        elif self.state == "VERT": colors["VERT"] = "#00FF00" # Lime green

        self._draw_circle(self.y + 35, colors["ROUGE"])
        self._draw_circle(self.y + 5, colors["ORANGE"])
        self._draw_circle(self.y - 25, colors["VERT"])    



    def _draw_circle(self, y_pos, color):
        self.pen.goto(self.x, y_pos)
        self.pen.dot(20, color) # Dessine un point de diamètre 20    

    def change_state(self):
        """Logique de cycle : Vert -> Orange -> Rouge -> Vert"""
        if self.state == "VERT":
            self.state = "ORANGE"
        elif self.state == "ORANGE":
            self.state = "ROUGE"
        elif self.state == "ROUGE":
            self.state = "VERT"
        
        self.timer = 0 # Reset du timer
        self.update_visuals()

        
    def update(self):
        """Appelé à chaque frame par le main."""
        self.timer += 1
        limit = self.durations.get(self.state, 100)
        
        if self.timer >= limit:
            self.change_state()