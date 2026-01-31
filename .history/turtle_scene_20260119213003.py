import turtle

class SceneBuilder:
    def __init__(self):
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0)

    def draw_background(self):
        """Dessine l'herbe."""
        turtle.bgcolor("darkgreen")

    def draw_roads(self):
        """Dessine les routes et le marquage au sol."""
        self.pen.penup()
        
        # 1. Le Bitume (Gris)
        self.pen.color("gray")
        
        # Route Horizontale (Est-Ouest)
        self.pen.goto(-400, -50)
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(800)
            self.pen.left(90)
            self.pen.forward(100)
            self.pen.left(90)
        self.pen.end_fill()

        # Route Verticale (Nord-Sud)
        self.pen.goto(-50, -300)
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(100)
            self.pen.left(90)
            self.pen.forward(600)
            self.pen.left(90)
        self.pen.end_fill()

        # 2. Les Lignes d'Arrêt (Blanches)
        self.pen.color("white")
        self.pen.width(5)
        
        # Ligne Stop Ouest (x=-60)
        self.draw_line(-60, -50, -60, 50)
        # Ligne Stop Est (x=60)
        self.draw_line(60, -50, 60, 50)
        # Ligne Stop Nord (y=60)
        self.draw_line(-50, 60, 50, 60)
        # Ligne Stop Sud (y=-60)
        self.draw_line(-50, -60, 50, -60)

    def draw_line(self, x1, y1, x2, y2):
        self.pen.penup()
        self.pen.goto(x1, y1)
        self.pen.pendown()
        self.pen.goto(x2, y2)
        self.pen.penup()