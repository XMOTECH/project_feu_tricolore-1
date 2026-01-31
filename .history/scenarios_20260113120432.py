from abc import ABC, abstractmethod

class ScenarioStrategy(ABC):
    """Classe abstraite définissant le contrat des scénarios."""
    
    @abstractmethod
    def get_light_durations(self):
        pass

    @abstractmethod
    def get_spawn_rate(self):
        pass

class NormalScenario(ScenarioStrategy):
    def get_light_durations(self):
        return {"green": 50, "orange": 20, "red": 50}
    
    def get_spawn_rate(self):
        return 0.02

# Nous ajouterons les autres (Nuit, Pointe, Manuel) plus tard