import turtle
import time
from turtle_scene import SceneBuilder
from intersection_controller import IntersectionController
from vehicles import VehicleManager
from gui import InterfaceManager
from scenarios import NormalScenario, RushHourScenario, NightScenario, ManualScenario
from logger import Logger

class SimulationController:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.title("Simulation Carrefour - Projet L3 ")
        self.screen.setup(width=900, height=700)
        self.screen.tracer(0)

        # Construction de la scène
        self.scene = SceneBuilder()
        self.scene.draw_background()
        self.scene.draw_roads()
        self.scene.draw_decorations()
        
        # Interface utilisateur
        self.gui = InterfaceManager()
        self.gui.draw_controls()
        
        # Contrôleur d'intersection (4 feux synchronisés)
        self.intersection = IntersectionController()
        
        # Logger
        self.logger = Logger()
        
        # Gestionnaire de véhicules (avec référence à l'écran pour les images)
        self.veh_manager = VehicleManager(self.screen, self.logger)
        
        # État de la simulation
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()
        self.total_paused_time = 0
        self.pause_start = 0

        # Scénarios disponibles
        self.scenarios = {
            "SCENARIO_1": NormalScenario(),
            "SCENARIO_2": RushHourScenario(),
            "SCENARIO_3": NightScenario(),
            "SCENARIO_4": ManualScenario()
        }
        self.current_scenario = self.scenarios["SCENARIO_1"]
        self.gui.set_active_scenario("SCENARIO_1")
        
        # Log du démarrage
        self.logger.log_event("SYSTEM", "Démarrage Application (Mode Amélioré)", 
                              self.intersection, self.current_scenario.name)

        self.screen.onclick(self.handle_mouse_click)
        
        # Gestion du survol (Hover)
        canvas = self.screen.getcanvas()
        canvas.bind('<Motion>', self.handle_mouse_move)

    def handle_mouse_move(self, event):
        # Conversion coordonnées Tkinter -> Turtle
        # (0,0) Tkinter = Coin haut-gauche
        # (0,0) Turtle = Centre
        canvas_width = self.screen.window_width()
        canvas_height = self.screen.window_height()
        
        x = event.x - canvas_width / 2
        y = canvas_height / 2 - event.y
        
        self.gui.handle_hover(x, y)

    def handle_mouse_click(self, x, y):
        action = self.gui.handle_click(x, y)
        
        if not action: 
            return

        # Log de l'interaction utilisateur
        self.logger.log_event("USER_INPUT", f"Clic sur {action}", 
                              self.intersection, self.current_scenario.name)

        if action == "PAUSE":
            if not self.is_paused:
                self.is_paused = True
                self.pause_start = time.time()
        elif action == "PLAY":
            if self.is_paused:
                self.is_paused = False
                self.total_paused_time += (time.time() - self.pause_start)
        elif action == "STOP":
            self.is_running = False
            self.logger.log_event("SYSTEM", "Arrêt Application", 
                                  self.intersection, self.current_scenario.name)
        elif action == "RESET":
            self._reset_simulation()

        elif action in self.scenarios:
            self.current_scenario = self.scenarios[action]
            self.gui.set_active_scenario(action)
            
            # Gestion du Mode Nuit (Visuels)
            is_night = (action == "SCENARIO_3")
            self.scene.toggle_night_mode(is_night)
            self.veh_manager.toggle_night_mode(is_night)
            self.gui.toggle_night_mode(is_night)
            self.intersection.redraw() # S'assurer que les feux sont au-dessus de la route
            
            self.logger.log_event("SCENARIO", f"Changement vers {self.current_scenario.name}", 
                                  self.intersection, self.current_scenario.name)

        elif action == "MANUAL_CLICK":
            if isinstance(self.current_scenario, ManualScenario):
                self.intersection.manual_change()
                self.logger.log_event("TRAFFIC_LIGHT", 
                                      f"Changement Manuel vers {self.intersection.current_phase}", 
                                      self.intersection, self.current_scenario.name)

    def _reset_simulation(self):
        """Réinitialise la simulation."""
        # Supprimer tous les véhicules
        for v in self.veh_manager.vehicles:
            v.shape.hideturtle()
        self.veh_manager.vehicles.clear()
        self.veh_manager.next_id = 1
        
        # Réinitialiser l'intersection
        self.intersection.phase_index = 0
        self.intersection.current_phase = "A"
        self.intersection.timer = 0
        self.intersection._apply_phase()
        
        self.current_scenario = self.scenarios["SCENARIO_1"]
        self.gui.set_active_scenario("SCENARIO_1")
        
        self.is_paused = True
        self.start_time = time.time()
        self.total_paused_time = 0
        self.pause_start = time.time()
        self.logger.log_event("SYSTEM", "Réinitialisation", 
                              self.intersection, self.current_scenario.name)

    def update_dashboard_data(self):
        """Calcule et envoie les stats à l'interface GUI."""
        # 1. Calcul du temps écoulé
        if not self.is_paused:
            elapsed = time.time() - self.start_time - self.total_paused_time
        else:
            elapsed = self.pause_start - self.start_time - self.total_paused_time
            
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # 2. Comptage véhicules
        v_count = len(self.veh_manager.vehicles)
        
        # 3. Calcul Fluidité (%)
        if v_count > 0:
            total_ratio = 0
            for v in self.veh_manager.vehicles:
                ratio = (v.current_speed / v.max_speed) if v.max_speed > 0 else 0
                total_ratio += ratio
            fluidity = int((total_ratio / v_count) * 100)
        else:
            fluidity = 100
            
        # 4. Envoi au GUI
        self.gui.update_stats(
            vehicles=v_count,
            time_str=time_str,
            fluidity=fluidity,
            phase=self.intersection.current_phase,
            scenario=self.current_scenario.name
        )

    def run(self):
        previous_phase = self.intersection.current_phase

        while self.is_running:
            if not self.is_paused:
                # Mise à jour de l'intersection
                self.intersection.update(self.current_scenario)
                
                # Mise à jour des véhicules
                self.veh_manager.update_vehicles(self.intersection)

                # Détection changement de phase
                if self.intersection.current_phase != previous_phase:
                    self.logger.log_event("TRAFFIC_LIGHT", 
                                          f"Phase passée à {self.intersection.current_phase}", 
                                          self.intersection, self.current_scenario.name)
                    previous_phase = self.intersection.current_phase
            
            # Mise à jour Tableau de Bord via GUI
            self.update_dashboard_data()
            
            self.screen.update()
            time.sleep(0.02)

if __name__ == "__main__":
    app = SimulationController()
    app.run()