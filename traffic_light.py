import turtle

class TrafficLight:
    def __init__(self, x, y, direction="EST", size_scale=1.0):
        self.x = x
        self.y = y
        self.direction = direction
        self.state = "ROUGE"
        self.timer = 0
        self.size_scale = size_scale

        # Configuration visuelle
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0)
        self.pen.penup()
        
        # Durées (en frames, approx 50 frames = 1 seconde)
        self.durations = {"VERT": 100, "ORANGE": 40, "ROUGE": 100}
        
        self.redraw()
        
    def redraw(self):
        """Redessine tout le bloc du feu."""
        self.pen.clear()
        self.draw_housing()
        self.update_visuals()
        
    def _draw_rect(self, x, y, w, h, color):
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.color(color)
        self.pen.begin_fill()
        for _ in range(2):
            self.pen.forward(w)
            self.pen.left(90)
            self.pen.forward(h)
            self.pen.left(90)
        self.pen.end_fill()

    def _draw_dot(self, x, y, size, color):
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.dot(size, color)

    def draw_housing(self):
        """Dessine le boîtier du feu (compact)."""
        scale = self.size_scale
        width = int(20 * scale)
        height = int(60 * scale)
        
        self._draw_rect(self.x - width/2, self.y - height/2, width, height, "black")

    def update_visuals(self):
        """Allume le bon cercle selon l'état."""
        colors = {"ROUGE": "darkred", "ORANGE": "sienna", "VERT": "darkgreen"}
        
        if self.state == "ROUGE": colors["ROUGE"] = "red"
        elif self.state == "ORANGE": colors["ORANGE"] = "orange"
        elif self.state == "VERT": colors["VERT"] = "#00FF00"
        elif self.state == "ETEINT": pass  # Tout reste sombre

        scale = self.size_scale
        spacing = int(18 * scale)
        dot_size = int(14 * scale)
        
        self._draw_dot(self.x, self.y + spacing, dot_size, colors["ROUGE"])
        self._draw_dot(self.x, self.y, dot_size, colors["ORANGE"])
        self._draw_dot(self.x, self.y - spacing, dot_size, colors["VERT"])

    def _draw_circle(self, y_pos, color, size=14):
        """Méthode gardée pour compatibilité."""
        self._draw_dot(self.x, y_pos, size, color)

    def set_state(self, new_state):
        """Change l'état du feu (utilisé par IntersectionController)."""
        if self.state != new_state:
            self.state = new_state
            self.update_visuals()

    def change_state(self):
        """Logique de cycle : Vert -> Orange -> Rouge -> Vert"""
        if self.state == "VERT":
            self.state = "ORANGE"
        elif self.state == "ORANGE":
            self.state = "ROUGE"
        elif self.state == "ROUGE":
            self.state = "VERT"
        else:
            self.state = "ROUGE"
        
        self.timer = 0
        self.update_visuals()

    def update(self, scenario_strategy):
        """Délègue la logique de mise à jour au scénario actif."""
        scenario_strategy.update_light(self)

    def manual_change(self):
        """Déclenche manuellement le changement d'état."""
        self.change_state()