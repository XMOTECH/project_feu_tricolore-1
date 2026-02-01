import turtle
import random

class SceneBuilder:
    def __init__(self):
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0)
        self.night_mode = False
        
        # Palettes de couleurs
        self.colors = {
            "day": {
                "grass": "#1b5e20", "asphalt": "#37474f", "lawn": "#2e7d32", 
                "bitumen": "#263238", "curb": "#455a64", "marking": "#eceff1",
                "yellow": "#fdd835", "house": "#795548"
            },
            "night": {
                "grass": "#0a1f0c", "asphalt": "#1c2326", "lawn": "#0d2610", 
                "bitumen": "#0f1416", "curb": "#263238", "marking": "#546e7a",
                "yellow": "#c0ca33", "house": "#263238"
            }
        }

    def toggle_night_mode(self, is_night):
        """Bascule entre le mode jour et nuit et redessine la scène."""
        self.night_mode = is_night
        self.pen.clear()
        self.draw_background()
        self.draw_roads()
        self.draw_decorations()

    def draw_background(self):
        """Dessine l'herbe et le fond."""
        c = self.colors["night" if self.night_mode else "day"]
        turtle.bgcolor(c["grass"])

    def draw_roads(self):
        """Dessine les routes en croix avec marquages professionnels."""
        self._draw_asphalt()
        self._draw_sidewalks_refined()
        self._draw_lane_markings()
        self._draw_lane_arrows()
        self._draw_pedestrian_signs()
        self._draw_crosswalks()
        self._draw_stop_lines()

    def _draw_pedestrian_signs(self):
        """Dessine des panneaux de passage piéton (diamants jaunes)."""
        sign_positions = [(-90, 90), (90, 90), (-90, -90), (90, -90)]
        for x, y in sign_positions:
            self._draw_diamond_sign(x, y)

    def _draw_diamond_sign(self, x, y):
        """Dessine un panneau de signalisation en losange."""
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.color("#fdd835")
        self.pen.setheading(45)
        self.pen.begin_fill()
        for _ in range(4):
            self.pen.forward(12)
            self.pen.left(90)
        self.pen.end_fill()
        self.pen.goto(x, y + 8)
        self.pen.color("black")
        self.pen.dot(4)
        self.pen.setheading(0)

    def _draw_asphalt(self):
        """Dessine l'asphalte gris des routes (pleine largeur)."""
        c = self.colors["night" if self.night_mode else "day"]
        self.pen.penup()
        self.pen.color(c["asphalt"])
        for x, y, w, h in [(-1000, -70, 2000, 140), (-70, -1000, 140, 2000)]:
            self.pen.goto(x, y)
            self.pen.begin_fill()
            for _ in range(2):
                self.pen.forward(w); self.pen.left(90)
                self.pen.forward(h); self.pen.left(90)
            self.pen.end_fill()

    def _draw_sidewalks_refined(self):
        """Dessine les trottoirs bitumés (60px) avec une perfection géométrique ENGINEERING."""
        palette = self.colors["night" if self.night_mode else "day"]
        LAWN = palette["lawn"]
        BITUMEN = palette["bitumen"]
        CURB = palette["curb"]
        
        # 1. Remplissage des Fonds (Pelouses)
        self.pen.color(LAWN)
        def draw_rect(x1, y1, x2, y2):
            self.pen.penup(); self.pen.goto(x1, y1); self.pen.begin_fill()
            for p in [(x2, y1), (x2, y2), (x1, y2), (x1, y1)]:
                self.pen.goto(p)
            self.pen.end_fill()
            
        draw_rect(-1000, 130, -130, 1000) 
        draw_rect(130, 130, 1000, 1000)   
        draw_rect(-1000, -1000, -130, -130) 
        draw_rect(130, -1000, 1000, -130)  

        # 2. Logiciel de dessin des Blocs avec angles corrigés
        def draw_sidewalk_corner(sx, sy, h_start, circle_r):
            # Remplissage Bitume
            self.pen.penup()
            self.pen.goto(70 * sx, 1000 * sy)
            self.pen.color(BITUMEN)
            self.pen.begin_fill()
            self.pen.goto(70 * sx, 130 * sy)
            self.pen.setheading(h_start)
            self.pen.circle(circle_r, 90)
            self.pen.goto(1000 * sx, 70 * sy)
            self.pen.goto(1000 * sx, 130 * sy)
            self.pen.goto(130 * sx, 130 * sy)
            self.pen.goto(130 * sx, 1000 * sy)
            self.pen.end_fill()
            
            # Bordure Intérieure (Côté Route)
            self.pen.pensize(2); self.pen.color(CURB)
            self.pen.penup(); self.pen.goto(70 * sx, 1000 * sy); self.pen.pendown()
            self.pen.goto(70 * sx, 130 * sy); self.pen.setheading(h_start)
            self.pen.circle(circle_r, 90); self.pen.goto(1000 * sx, 70 * sy)
            self.pen.penup()
            
            # Bordure Extérieure (Côté Pelouse - Trait pour angles)
            self.pen.goto(130 * sx, 1000 * sy); self.pen.pendown()
            self.pen.goto(130 * sx, 130 * sy); self.pen.goto(1000 * sx, 130 * sy)
            self.pen.penup(); self.pen.pensize(1)

        draw_sidewalk_corner(-1, 1, 270, -60) 
        draw_sidewalk_corner(1, 1, 270, 60)   
        draw_sidewalk_corner(-1, -1, 90, 60)  
        draw_sidewalk_corner(1, -1, 90, -60)  
        self.pen.setheading(0)

    def _draw_lane_arrows(self):
        """Dessine des flèches directionnelles sur les voies."""
        self.pen.color("#eceff1")
        self._draw_arrow(-300, -35, 0)
        self._draw_arrow(300, 35, 180)
        self._draw_arrow(35, -300, 90)
        self._draw_arrow(-35, 300, 270)

    def _draw_arrow(self, x, y, heading):
        self.pen.penup(); self.pen.goto(x, y); self.pen.setheading(heading); self.pen.pendown()
        self.pen.pensize(4); self.pen.forward(25); self.pen.left(135)
        self.pen.forward(10); self.pen.backward(10); self.pen.right(270)
        self.pen.forward(10); self.pen.penup(); self.pen.pensize(1); self.pen.setheading(0)

    def _draw_lane_markings(self):
        """Dessine les lignes de voies."""
        palette = self.colors["night" if self.night_mode else "day"]
        # Doubles Jaunes
        self.pen.pensize(2); self.pen.color(palette["yellow"])
        for offset in [-2, 2]:
            for orientation in [0, 90]:
                self.pen.setheading(orientation)
                self.pen.penup()
                if orientation == 0:
                    self.pen.goto(-1000, offset); self.pen.pendown()
                    self.pen.goto(-100, offset); self.pen.penup()
                    self.pen.goto(100, offset); self.pen.pendown(); self.pen.goto(1000, offset)
                else:
                    self.pen.goto(offset, -1000); self.pen.pendown()
                    self.pen.goto(offset, -100); self.pen.penup()
                    self.pen.goto(offset, 100); self.pen.pendown(); self.pen.goto(offset, 1000)
        
        # Pointillés Blancs
        self.pen.color(palette["marking"]); self.pen.pensize(1)
        for y in [-35, 35]:
            for x in range(-1000, 1000, 40):
                if -100 < x < 100: continue
                self.pen.penup(); self.pen.goto(x, y); self.pen.pendown(); self.pen.setheading(0); self.pen.forward(20)
        for x in [-35, 35]:
            for y in range(-1000, 1000, 40):
                if -100 < y < 100: continue
                self.pen.penup(); self.pen.goto(x, y); self.pen.pendown(); self.pen.setheading(90); self.pen.forward(20)

    def _draw_crosswalks(self):
        """Dessine les passages piétons."""
        palette = self.colors["night" if self.night_mode else "day"]
        self.pen.color(palette["marking"])
        for i in range(7):
            self._draw_zebra_stripe(-60 + i*20, 85, 40, 12, 90)   # N
            self._draw_zebra_stripe(-60 + i*20, -125, 40, 12, 90) # S
            self._draw_zebra_stripe(85, -60 + i*20, 40, 12, 0)    # E
            self._draw_zebra_stripe(-125, -60 + i*20, 40, 12, 0)  # O

    def _draw_zebra_stripe(self, x, y, w, h, heading):
        self.pen.penup(); self.pen.goto(x, y); self.pen.setheading(heading); self.pen.begin_fill()
        for _ in range(2): self.pen.forward(w); self.pen.left(90); self.pen.forward(h); self.pen.left(90)
        self.pen.end_fill(); self.pen.setheading(0)

    def _draw_stop_lines(self):
        """Dessine les lignes d'arrêt."""
        palette = self.colors["night" if self.night_mode else "day"]
        self.pen.color(palette["marking"]); self.pen.pensize(6)
        stops = [(-135, -70, -135, 0), (135, 70, 135, 0), (0, -135, 70, -135), (0, 135, -70, 135)]
        for x1, y1, x2, y2 in stops:
            self.pen.penup(); self.pen.goto(x1, y1); self.pen.pendown(); self.pen.goto(x2, y2)
        self.pen.penup(); self.pen.pensize(1)

    def _draw_house(self, x, y, color):
        """Dessine une maison résidentielle."""
        palette = self.colors["night" if self.night_mode else "day"]
        house_color = palette["house"] if self.night_mode else color
        self.pen.penup(); self.pen.goto(x, y); self.pen.color(house_color); self.pen.begin_fill()
        for _ in range(2): self.pen.forward(90); self.pen.left(90); self.pen.forward(70); self.pen.left(90)
        self.pen.end_fill()
        self.pen.goto(x - 10, y + 70); self.pen.color("#4e342e"); self.pen.begin_fill()
        self.pen.goto(x + 45, y + 105); self.pen.goto(x + 100, y + 70); self.pen.goto(x - 10, y + 70); self.pen.end_fill()
        self.pen.color("#eceff1" if not self.night_mode else "#fff59d"); self.pen.goto(x + 30, y + 25); self.pen.dot(20)

    def draw_decorations(self):
        """Ajoute juste le petit cercle au centre du carrefour."""
        self._draw_central_island()

    def _draw_central_island(self):
        """Dessine un îlot central circulaire réduit pour laisser passer les véhicules."""
        # Bordure granit (Rayon réduit à 22)
        self.pen.penup(); self.pen.goto(0, -22); self.pen.color("#90a4ae")
        self.pen.begin_fill(); self.pen.circle(22); self.pen.end_fill()
        # Centre herbeux (Rayon réduit à 18)
        self.pen.penup(); self.pen.goto(0, -18); self.pen.color("#1b5e20")
        self.pen.begin_fill(); self.pen.circle(18); self.pen.end_fill()

    def _draw_street_lamp(self, x, y):
        """Lampadaire avec halo."""
        self.pen.penup(); self.pen.goto(x, y)
        for s, c in [(40, "#fff9c4"), (25, "#fff59d"), (12, "#ffee58")]:
            self.pen.color(c); self.pen.dot(s)
        self.pen.color("#37474f"); self.pen.dot(10)
        self.pen.color("#90a4ae"); self.pen.dot(5)
