import turtle

class Button:
    def __init__(self, label, x, y, w, h, color, action_code):
        self.label = label
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.action_code = action_code # Identifiant de l'action (ex: "PLAY", "PAUSE")

    def draw(self, pen):
        # Dessin du rectangle
        pen.penup()
        pen.goto(self.x, self.y)
        pen.fillcolor(self.color)
        pen.begin_fill()
        for _ in range(2):
            pen.forward(self.w)
            pen.left(90)
            pen.forward(self.h)
            pen.left(90)
        pen.end_fill()
        
        # Dessin du texte
        pen.color("white")
        pen.goto(self.x + self.w/2, self.y + self.h/4)
        pen.write(self.label, align="center", font=("Arial", 10, "bold"))

    def is_clicked(self, x, y):
        """Vérifie si le clic (x,y) est dans le rectangle du bouton."""
        return (self.x <= x <= self.x + self.w) and (self.y <= y <= self.y + self.h)

class InterfaceManager:
    def __init__(self):
        self.buttons = []
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0)
        self.pen.penup()
        
        # Création des boutons (Label, x, y, width, height, color, code)
        self.buttons.append(Button("PLAY", -350, 250, 60, 30, "green", "PLAY"))
        self.buttons.append(Button("PAUSE", -280, 250, 60, 30, "orange", "PAUSE"))
        self.buttons.append(Button("STOP", -210, 250, 60, 30, "red", "STOP"))
        self.buttons.append(Button("RESET", -140, 250, 60, 30, "blue", "RESET"))

    def draw_controls(self):
        """Dessine tous les boutons."""
        self.pen.clear()
        for btn in self.buttons:
            btn.draw(self.pen)

    def handle_click(self, x, y):
        """Retourne l'action si un bouton est cliqué, sinon None."""
        for btn in self.buttons:
            if btn.is_clicked(x, y):
                print(f"[GUI] Bouton cliqué : {btn.action_code}")
                return btn.action_code
        return None