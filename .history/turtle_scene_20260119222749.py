import turtle

class SceneBuilder:
    def __init__(self):
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0) # Vitesse max pour le dessin instantané

    def draw_background(self):
        """Dessine l'herbe et le fond."""
        turtle.bgcolor("darkgreen")

    def draw_roads(self):
        """Dessine les routes en croix."""
        self.pen.penup()
        self.pen.color("gray")
        
        # Route Horizontale
        self.pen.goto(-400, -50)
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(800)
            self.pen.left(90)
            self.pen.forward(100)
            self.pen.left(90)
        self.pen.end_fill()

        # Route Verticale
        self.pen.goto(-50, -300)
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(100)
            self.pen.left(90)
            self.pen.forward(600)
            self.pen.left(90)
        self.pen.end_fill()