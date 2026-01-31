from abc import ABC, abstractmethod

class ScenarioStrategy(ABC):
    def __init__(self):
        self.name = "Inconnu"
        self.timer = 0 # Timer global du carrefour

    @abstractmethod
    def update_lights(self, lights_dict):
        """
        lights_dict attendu : 
        {
            'NS': [feu_nord, feu_sud], 
            'EW': [feu_est, feu_ouest]
        }
        """
        pass

class NormalScenario(ScenarioStrategy):
    def __init__(self):
        super().__init__()
        self.name = "Normal (Synchro)"
        # Cycle total : 300 frames (~6 secondes)
        # 0-100   : NS Vert   | EW Rouge
        # 100-130 : NS Orange | EW Rouge
        # 130-150 : TOUT ROUGE (Sécurité)
        # 150-250 : NS Rouge  | EW Vert
        # 250-280 : NS Rouge  | EW Orange
        # 280-300 : TOUT ROUGE (Sécurité)

    def update_lights(self, lights_dict):
        self.timer += 1
        cycle_time = self.timer % 300 # Boucle infinie de 0 à 299

        # Détermination des états cibles
        state_ns = "ROUGE"
        state_ew = "ROUGE"

        if 0 <= cycle_time < 100:
            state_ns = "VERT"
            state_ew = "ROUGE"
        elif 100 <= cycle_time < 130:
            state_ns = "ORANGE"
            state_ew = "ROUGE"
        elif 130 <= cycle_time < 150:
            state_ns = "ROUGE" # Tampon sécurité
            state_ew = "ROUGE"
        elif 150 <= cycle_time < 250:
            state_ns = "ROUGE"
            state_ew = "VERT"
        elif 250 <= cycle_time < 280:
            state_ns = "ROUGE"
            state_ew = "ORANGE"
        # 280-300 reste ROUGE/ROUGE par défaut

        # Application aux feux réels
        self._apply_state(lights_dict['NS'], state_ns)
        self._apply_state(lights_dict['EW'], state_ew)

    def _apply_state(self, lights_list, state):
        for light in lights_list:
            if light.state != state:
                light.state = state
                light.update_visuals()

class RushHourScenario(NormalScenario):
    def __init__(self):
        super().__init__()
        self.name = "Heure de Pointe"
        # On pourrait surcharger update_lights ici pour privilégier l'axe Est-Ouest
        # Pour l'instant, on garde la même logique pour tester l'architecture.

class NightScenario(ScenarioStrategy):
    def __init__(self):
        super().__init__()
        self.name = "Mode Nuit"

    def update_lights(self, lights_dict):
        self.timer += 1
        # Clignotement Orange global
        state = "ORANGE" if (self.timer // 30) % 2 == 0 else "ETEINT"
        
        self._apply_state(lights_dict['NS'], state)
        self._apply_state(lights_dict['EW'], state)

class ManualScenario(ScenarioStrategy):
    def __init__(self):
        super().__init__()
        self.name = "Manuel"
        self.current_phase = 0 # 0: NS Green, 1: EW Green

    def update_lights(self, lights_dict):
        # En manuel, on ne fait rien automatiquement.
        # C'est main.py qui appellera switch_phase()
        pass

    def switch_phase(self, lights_dict):
        self.current_phase = (self.current_phase + 1) % 2
        
        if self.current_phase == 0:
            self._apply_state(lights_dict['NS'], "VERT")
            self._apply_state(lights_dict['EW'], "ROUGE")
        else:
            self._apply_state(lights_dict['NS'], "ROUGE")
            self._apply_state(lights_dict['EW'], "VERT")