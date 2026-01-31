import turtle
import time
from turtle_scene import SceneBuilder
from traffic_light import TrafficLight
from vehicles import Vehicle, VehicleManager
from gui import InterfaceManager

class SimulationController:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.title("Simulation Feu Tricolore - Projet L3")
        self.screen.setup(width=800, height=600)
        self.screen.tracer(0)

        self.scene = SceneBuilder()
        self.gui = InterfaceManager()
        self.traffic_light = TrafficLight(0, 0)
        self.veh_manager = VehicleManager()
        
        # État de la simulation
        self.is_running = True
        self.is_paused = False # Nouvelle variable d'état

        self.scene.draw_background()
        self.scene.draw_roads()
        self.gui.draw_controls()

        # Voiture de test
        self.test_car = Vehicle(1, -350, -20)
        self.veh_manager.vehicles.append(self.test_car)

        # C'est ici qu'on active l'écoute de la souris
        self.screen.onclick(self.handle_mouse_click)

    def handle_mouse_click(self, x, y):
        """Appelé automatiquement par Turtle lors d'un clic."""
        action = self.gui.handle_click(x, y)
        
        if action == "PAUSE":
            self.is_paused = True
            print("Simulation en PAUSE")
        elif action == "PLAY":
            self.is_paused = False
            print("Simulation en LECTURE")
        elif action == "STOP":
            self.is_running = False
            print("Arrêt du programme...")
        elif action == "RESET":
            # On remet la voiture au début pour tester
            self.test_car.x = -350
            self.test_car.current_speed = self.test_car.max_speed
            self.traffic_light.state = "ROUGE"
            self.traffic_light.timer = 0
            self.traffic_light.update_visuals()
            self.is_paused = True # On attend Play pour repartir
            print("Simulation réinitialisée")

    def run(self):
        while self.is_running:
            # Si on n'est PAS en pause, on met à jour la logique
            if not self.is_paused:
                self.traffic_light.update()
                self.veh_manager.update_vehicles(self.traffic_light)
            
            self.screen.update()
            time.sleep(0.02)

if __name__ == "__main__":
    app = SimulationController()
    app.run()