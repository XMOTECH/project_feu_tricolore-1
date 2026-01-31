import turtle
import time
from turtle_scene import SceneBuilder
from traffic_light import TrafficLight
from vehicles import Vehicle, VehicleManager
from gui import InterfaceManager

class SimulationController:
    def __init__(self):
        # 1. Configuration de la fenêtre
        self.screen = turtle.Screen()
        self.screen.title("Simulation Feu Tricolore - Projet L3")
        self.screen.setup(width=800, height=600)
        self.screen.tracer(0) # Désactive l'animation auto (fluidité max)

        # 2. Initialisation des modules
        self.scene = SceneBuilder()
        self.gui = InterfaceManager()
        self.traffic_light = TrafficLight(0, 0)
        self.veh_manager = VehicleManager()

        # 3. Dessin statique initial
        self.scene.draw_background()
        self.scene.draw_roads()
        self.gui.draw_controls()

        # Test: Création d'une voiture manuelle pour vérifier l'animation
        self.test_car = Vehicle(1, -350, -20)
        self.veh_manager.vehicles.append(self.test_car)

        self.is_running = True

    def run(self):
        """Boucle principale de la simulation."""
        while self.is_running:
            # Mise à jour logique
            self.veh_manager.update_vehicles()
            
            # Rafraîchissement écran
            self.screen.update()
            time.sleep(0.02) # ~50 FPS

if __name__ == "__main__":
    app = SimulationController()
    app.run()