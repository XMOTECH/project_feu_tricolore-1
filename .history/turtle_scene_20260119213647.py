import turtle

class SceneBuilder:
    def __init__(self):
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0) 

        # Palette de couleurs "Pro"
        self.COLOR_GRASS = "#4F7942"   # Vert fougère (plus naturel)
        self.COLOR_ROAD = "#3A3A3A"    # Gris bitume foncé
        self.COLOR_MARKING = "#E0E0E0" # Blanc signalisation (pas blanc pur)
        self.COLOR_SIDEWALK = "#707070" # Gris béton trottoir

    def draw_background(self):
        """Dessine l'herbe de fond."""
        turtle.bgcolor(self.COLOR_GRASS)

    def draw_roads(self):
        """Dessine une infrastructure réaliste."""
        self.pen.penup()
        
        # 1. D'abord, on dessine une immense croix de bitume
        self.pen.color(self.COLOR_ROAD)
        
        # Axe Horizontal (Est-Ouest)
        self.pen.goto(-400, -70) # Route plus large (140px)
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(800)
            self.pen.left(90)
            self.pen.forward(140)
            self.pen.left(90)
        self.pen.end_fill()

        # Axe Vertical (Nord-Sud)
        self.pen.goto(-70, -300)
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(140)
            self.pen.left(90)
            self.pen.forward(600)
            self.pen.left(90)
        self.pen.end_fill()

        # 2. Les "Coins arrondis" (Astuce technique)
        # On redessine de l'herbe + trottoir dans les coins pour arrondir le carrefour
        corner_radius = 40
        offsets = [
            (-70, 70, 90),   # Haut Gauche
            (70, 70, 0),     # Haut Droite
            (70, -70, -90),  # Bas Droite
            (-70, -70, 180)  # Bas Gauche
        ]
        
        for x, y, angle in offsets:
            self.draw_curbed_corner(x, y, angle, corner_radius)

        # 3. Marquage au sol (Détails)
        self.draw_markings()

    def draw_curbed_corner(self, x, y, angle, radius):
        """Dessine un coin de trottoir arrondi."""
        self.pen.setheading(angle)
        self.pen.goto(x, y)
        self.pen.color(self.COLOR_GRASS) # Couleur de fond pour "effacer" le bitume en trop
        self.pen.begin_fill()
        
        # On dessine un carré qui part du coin vers l'extérieur
        self.pen.forward(10) # petit ajustement
        self.pen.left(90)
        self.pen.forward(10)
        # Mais on fait une courbe inverse pour simuler le trottoir
        # C'est complexe en turtle pur, on va faire plus simple :
        # On dessine juste un carré d'herbe aux coins de l'intersection 
        # pour "rogner" la route si on voulait faire simple.
        # Mais ici, on va dessiner le TROTTOIR (Gris clair)
        self.pen.end_fill()
        
        # Simplification visuelle : Des arcs de cercle gris clair pour les trottoirs
        self.pen.color(self.COLOR_SIDEWALK)
        self.pen.width(3)
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.pendown()
        # Dessine l'arrondi du trottoir
        if angle == 0:     self.pen.circle(-radius, 90)
        elif angle == 90:  self.pen.circle(-radius, 90)
        elif angle == 180: self.pen.circle(-radius, 90)
        elif angle == -90: self.pen.circle(-radius, 90)

    def draw_markings(self):
        self.pen.color(self.COLOR_MARKING)
        self.pen.width(2)

        # A. Lignes médianes discontinues (Dashed lines)
        # Horizontal
        self.draw_dashed_line(-400, 0, -80, 0) # Ouest
        self.draw_dashed_line(80, 0, 400, 0)   # Est
        # Vertical
        self.draw_dashed_line(0, 400, 0, 80)   # Nord
        self.draw_dashed_line(0, -80, 0, -300) # Sud

        # B. Passages Piétons (Zèbres)
        self.draw_zebra(-90, -70, "V") # Ouest
        self.draw_zebra(90, -70, "V")  # Est
        self.draw_zebra(-70, 90, "H")  # Nord
        self.draw_zebra(-70, -90, "H") # Sud

        # C. Lignes de Stop (Plus épaisses)
        self.pen.width(4)
        # Stop Ouest (x=-80)
        self.draw_line(-80, 0, -80, 70) 
        # Stop Est (x=80)
        self.draw_line(80, -70, 80, 0)
        # Stop Nord (y=80)
        self.draw_line(0, 80, -70, 80)
        # Stop Sud (y=-80)
        self.draw_line(70, -80, 0, -80)

    def draw_dashed_line(self, x1, y1, x2, y2):
        self.pen.penup()
        self.pen.goto(x1, y1)
        self.pen.setheading(self.pen.towards(x2, y2))
        
        dist = self.pen.distance(x2, y2)
        step = 20
        for _ in range(int(dist // step)):
            self.pen.pendown()
            self.pen.forward(10) # Trait
            self.pen.penup()
            self.pen.forward(10) # Vide

    def draw_zebra(self, x, y, orientation):
        """Dessine un passage piéton style 'Zèbre'."""
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.setheading(0)
        
        number_of_stripes = 6
        
        if orientation == "V": # Sur route horizontale
            for _ in range(number_of_stripes):
                self.draw_rect_filled(x, y + 10, 10, 14, self.COLOR_MARKING)
                y += 24
        else: # Sur route verticale
             for _ in range(number_of_stripes):
                self.draw_rect_filled(x + 10, y, 14, 10, self.COLOR_MARKING)
                x += 24

    def draw_rect_filled(self, x, y, w, h, color):
        prev_pos = self.pen.pos()
        self.pen.goto(x, y)
        self.pen.color(color)
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(w)
            self.pen.left(90)
            self.pen.forward(h)
            self.pen.left(90)
        self.pen.end_fill()
        self.pen.goto(prev_pos)

    def draw_line(self, x1, y1, x2, y2):
        self.pen.penup()
        self.pen.goto(x1, y1)
        self.pen.pendown()
        self.pen.goto(x2, y2)
        self.pen.penup()