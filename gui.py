import turtle
import os

class Button:
    def __init__(self, label, x, y, w, h, color_theme, action_code, tooltip=None, font_size=10):
        self.label = label
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.theme = color_theme
        self.action_code = action_code
        self.tooltip = tooltip
        self.font_size = font_size
        self.is_active = False
        
        # Palettes modernes et premium
        self.palettes = {
            "green":  {"bg": "#1b5e20", "border": "#69f0ae", "text": "white"},
            "orange": {"bg": "#e65100", "border": "#ffd740", "text": "white"},
            "red":    {"bg": "#b71c1c", "border": "#ff5252", "text": "white"},
            "blue":   {"bg": "#01579b", "border": "#40c4ff", "text": "white"},
            "purple": {"bg": "#4a148c", "border": "#e040fb", "text": "white"},
            "gray":   {"bg": "#212121", "border": "#424242", "text": "#bdbdbd"},
            "active": {"bg": "#26a69a", "border": "#ffffff", "text": "white"}
        }

    def draw(self, pen):
        theme_to_use = "active" if self.is_active else self.theme
        p = self.palettes.get(theme_to_use, self.palettes["gray"])
        
        # 1. Effet d'ombre/bordure lumineuse (Glow effect)
        if self.is_active:
            pen.penup(); pen.pensize(4); pen.color(p["border"])
            pen.goto(self.x - 1, self.y - 1); pen.pendown()
            self._rounded_rect(pen, self.w + 2, self.h + 2, 8)
            pen.penup()

        # 2. Fond du bouton (Arrondi)
        pen.penup(); pen.goto(self.x, self.y)
        pen.begin_fill(); pen.color(p["bg"])
        self._rounded_rect(pen, self.w, self.h, 6)
        pen.end_fill()
        
        # 3. Bordure fine
        pen.penup(); pen.pensize(1); pen.color(p["border"])
        pen.goto(self.x, self.y); pen.pendown()
        self._rounded_rect(pen, self.w, self.h, 6)
        pen.penup()

        # 4. Label (Centrage vertical corrigé pour les icônes)
        pen.penup(); pen.color(p["text"])
        # Ajustement fin pour Turtle : on décale légèrement vers le bas (-1 ou -2) car Turtle dessine souvent "haut"
        y_offset = (self.h - self.font_size) / 2 - 2
        pen.goto(self.x + self.w/2, self.y + y_offset)
        font_family = "Segoe UI" if os.name == 'nt' else "Verdana"
        pen.write(self.label, align="center", font=(font_family, self.font_size, "bold" if self.is_active else "normal"))

    def _rounded_rect(self, pen, w, h, r):
        """Dessine un rectangle arrondi."""
        pen.setheading(0)
        for _ in range(2):
            pen.forward(w-2*r)
            pen.circle(r, 90)
            pen.forward(h-2*r)
            pen.circle(r, 90)

    def is_clicked(self, x, y):
        return (self.x <= x <= self.x + self.w) and (self.y <= y <= self.y + self.h)

class InterfaceManager:
    def __init__(self):
        self.buttons = []
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.speed(0)
        self.pen.penup()
        
        self.tooltip_pen = turtle.Turtle()
        self.tooltip_pen.hideturtle()
        self.tooltip_pen.speed(0)
        self.tooltip_pen.penup()
        self.last_hovered = None
        self.night_mode = False # Par défaut jour
        
        y_top = 280
        y_bot = -300
        
        y_top = 275
        x_start = -550
        
        # Top Controls (Shifted Left) - Taille d'icône réduite pour éviter les débordements
        self.buttons.append(Button("▶",   x_start,      y_top, 85, 30, "green", "PLAY", tooltip="Démarrer", font_size=20))
        self.buttons.append(Button("⏸", x_start + 90, y_top, 85, 30, "orange", "PAUSE", tooltip="Pause", font_size=20))
        self.buttons.append(Button("■",  x_start + 180, y_top, 85, 30, "red", "STOP", tooltip="Arrêter", font_size=20))
        self.buttons.append(Button("↺",  x_start + 270, y_top, 85, 30, "blue", "RESET", tooltip="Réinitialiser", font_size=20))

        # Scenario Block - Bottom Left (Vertical)
        y_start = -160
        x_left = -542 # Adjusted for centering (Panel is at -555, width 175)
        self.buttons.append(Button("🌿 Normal",     x_left, y_start, 150, 30, "gray", "SCENARIO_1"))
        self.buttons.append(Button("🏙️ Pointe",     x_left, y_start - 40, 150, 30, "gray", "SCENARIO_2"))
        self.buttons.append(Button("🌙 Nuit",       x_left, y_start - 80, 150, 30, "gray", "SCENARIO_3"))
        self.buttons.append(Button("🎮 Manuel",     x_left, y_start - 120, 150, 30, "gray", "SCENARIO_4"))
        
        # Bouton Action (Manuel) - Restauré et centré
        self.buttons.append(Button("⚡ ACTIONS",    x_left, y_start - 180, 150, 35, "purple", "MANUAL_CLICK", tooltip="Changer de phase"))
        
        # Stats pour le tableau de bord
        self.stats = {
            "vehicles": 0,
            "time": "00:00",
            "fluidity": 100,
            "phase": "A",
            "scenario": "Normal"
        }
        
    def set_active_scenario(self, scenario_code):
        changed = False
        for btn in self.buttons:
            if btn.action_code.startswith("SCENARIO_"):
                was_active = btn.is_active
                btn.is_active = (btn.action_code == scenario_code)
                if was_active != btn.is_active:
                    changed = True
        
        if changed:
            self.draw_controls()

    def update_stats(self, vehicles, time_str, fluidity, phase, scenario):
        """Met à jour les données du tableau de bord."""
        self.stats["vehicles"] = vehicles
        self.stats["time"] = time_str
        self.stats["fluidity"] = fluidity
        self.stats["phase"] = phase
        self.stats["scenario"] = scenario
        self.draw_controls()

    def toggle_night_mode(self, is_night):
        """Bascule le style de l'interface."""
        self.night_mode = is_night
        self.draw_controls()

    def draw_controls(self):
        self.pen.clear()
        
        # Couleurs des panneaux (Simu Glassmorphism)
        if not self.night_mode:
            panel_bg = "#263238"  # Slate dark
            panel_border = "#455a64"
            title_color = "#e0f7fa"
            accent = "#00acc1"
        else:
            panel_bg = "#0a0c10"  # Deep black
            panel_border = "#00e5ff" # Cyan glow
            title_color = "#00e5ff"
            accent = "#00e5ff"
        
        # 1. Top Panel (Commandes)
        self._panel(-555, 270, 365, 75, panel_bg, panel_border)
        
        # Titre Commandes
        self.pen.penup(); self.pen.color(title_color)
        self.pen.goto(-372, 318)
        self.pen.write("COMMANDES", align="center", font=("Verdana", 9, "bold"))
        
        # Ligne de séparation Commandes
        self.pen.penup(); self.pen.pensize(1); self.pen.color(panel_border)
        self.pen.goto(-545, 310); self.pen.pendown()
        self.pen.goto(-300, 310); self.pen.penup()
        
        # 2. Left Panel (Scenarios)
        self._panel(-555, -380, 175, 280, panel_bg, panel_border)
        
        self.pen.penup(); self.pen.color(title_color)
        self.pen.goto(-467, -120)
        self.pen.write("CHOIX DU SCENARIO", align="center", font=("Verdana", 9, "bold"))
        
        self.pen.penup(); self.pen.pensize(1); self.pen.color(panel_border)
        self.pen.goto(-545, -125); self.pen.pendown()
        self.pen.goto(-390, -125); self.pen.penup()
        
        # 3. New Dashboard Panel (Top Right) - Agrandi et étendu vers le bas
        self._panel(160, 150, 280, 195, panel_bg, panel_border)
        
        # Titre Dashboard
        self.pen.penup(); self.pen.color(title_color)
        self.pen.goto(300, 318)
        self.pen.write("TABLEAU DE BORD", align="center", font=("Verdana", 10, "bold"))
        
        self.pen.penup(); self.pen.pensize(1); self.pen.color(panel_border)
        self.pen.goto(170, 310); self.pen.pendown()
        self.pen.goto(430, 310); self.pen.penup()
        
        # Affichage des Stats
        y_stats = 280
        x_label = 175
        x_val = 295
        
        stats_labels = [
            ("⏱ Temps",      self.stats["time"]),
            ("🚗 Véhicules",  f"{self.stats['vehicles']:02d}"),
            ("⚡ Fluidité",  f"{self.stats['fluidity']}%"),
            ("🚥 Phase",      self.stats["phase"]),
            ("🎭 Scénario",   self.stats["scenario"])
        ]
        
        for label, val in stats_labels:
            self.pen.goto(x_label, y_stats)
            self.pen.color("#90a4ae")
            self.pen.write(label, font=("Verdana", 12, "normal")) # Police 10 -> 12
            self.pen.goto(x_val, y_stats)
            self.pen.color("white")
            self.pen.write(f":  {val}", font=("Verdana", 12, "bold")) # Police 10 -> 12
            y_stats -= 26 # Espacement 22 -> 26

        for btn in self.buttons:
            btn.draw(self.pen)

    def _panel(self, x, y, w, h, bg, border=""):
        """Dessine un panneau de contrôle arrondi et élégant."""
        self.pen.penup()
        r = 10 # Rayon de l'arrondi
        
        # On s'assure que y est le bas et h est positif pour le remplissage
        # Notre dessin part de x,y (coin bas gauche)
        
        # Fond
        self.pen.goto(x+r, y); pen = self.pen
        pen.setheading(0)
        pen.begin_fill(); pen.color(bg)
        for _ in range(2):
            pen.forward(w-2*r); pen.circle(r, 90)
            pen.forward(h-2*r); pen.circle(r, 90)
        pen.end_fill()
        
        # Bordure
        if border:
            pen.pensize(2); pen.color(border); pen.penup()
            pen.goto(x+r, y); pen.pendown()
            for _ in range(2):
                pen.forward(w-2*r); pen.circle(r, 90)
                pen.forward(h-2*r); pen.circle(r, 90)
            pen.pensize(1); pen.penup()

    def handle_click(self, x, y):
        for btn in self.buttons:
            if btn.is_clicked(x, y):
                return btn.action_code
        return None

    def handle_hover(self, x, y):
        hovered_btn = None
        for btn in self.buttons:
            if btn.is_clicked(x, y) and btn.tooltip:
                hovered_btn = btn
                break
        
        if hovered_btn != self.last_hovered:
            self.last_hovered = hovered_btn
            self.tooltip_pen.clear()
            
            if hovered_btn:
                self.draw_tooltip(hovered_btn)

    def draw_tooltip(self, btn):
        x = btn.x + btn.w / 2
        y = btn.y - 20 # Espacement info-bulle
        
        text = btn.tooltip
        self.tooltip_pen.color("#00e5ff" if self.night_mode else "#fdd835")
        self.tooltip_pen.goto(x, y)
        self.tooltip_pen.write(text, align="center", font=("Verdana", 14, "bold"))