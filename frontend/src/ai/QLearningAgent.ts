export class QLearningAgent {
  public qTable: Record<string, [number, number]> = {};
  private alpha: number;
  private gamma: number;
  private epsilon: number;
  private actions: number[];
  private pendingUpdates: Record<string, [number, number]> = {};
  private backendUrl: string;

  constructor(
    actions: number[] = [0, 1],
    alpha = 0.1,
    gamma = 0.9,
    epsilon = 0.1,
    backendUrl = "http://localhost:8000"
  ) {
    self.addEventListener
    this.actions = actions; // 0: STAY, 1: SWITCH
    this.alpha = alpha;
    this.gamma = gamma;
    this.epsilon = epsilon;
    this.backendUrl = backendUrl;
  }

  /**
   * Convertit l'état en une clé de dictionnaire (string).
   */
  public getStateKey(
    nCount: number,
    sCount: number,
    eCount: number,
    oCount: number,
    currentPhase: string,
    timeInPhase: number
  ): string {
    // Discrétisation simple : 0, 1-2, 3-5, 6+
    const discretize = (count: number): number => {
      if (count === 0) return 0;
      if (count <= 2) return 1;
      if (count <= 5) return 2;
      return 3;
    };

    // Discrétisation du temps (par paliers de 20 frames)
    const timeDisc = Math.floor(timeInPhase / 20);

    return `${discretize(nCount)}_${discretize(sCount)}_${discretize(eCount)}_${discretize(oCount)}_${currentPhase}_${timeDisc}`;
  }

  /**
   * Choisit une action selon la politique epsilon-greedy.
   */
  public chooseAction(stateKey: string): number {
    if (!this.qTable[stateKey]) {
      this.qTable[stateKey] = [0.0, 0.0];
    }

    if (Math.random() < this.epsilon) {
      return Math.floor(Math.random() * this.actions.length);
    }

    // Action avec la valeur Q maximale
    const qValues = this.qTable[stateKey];
    return qValues[0] >= qValues[1] ? 0 : 1;
  }

  /**
   * Met à jour la table Q selon l'équation de Bellman.
   */
  public learn(state: string, action: number, reward: number, nextState: string): void {
    if (!this.qTable[state]) {
      this.qTable[state] = [0.0, 0.0];
    }
    if (!this.qTable[nextState]) {
      this.qTable[nextState] = [0.0, 0.0];
    }

    const oldVal = this.qTable[state][action];
    const nextMax = Math.max(...this.qTable[nextState]);

    // Formule de Bellman
    const newVal = (1 - this.alpha) * oldVal + this.alpha * (reward + this.gamma * nextMax);
    this.qTable[state][action] = newVal;

    // Enregistrer pour synchronisation par lots
    this.pendingUpdates[state] = this.qTable[state];
  }

  /**
   * Charge la Q-Table depuis le serveur FastAPI.
   */
  public async loadQTable(): Promise<void> {
    try {
      const response = await fetch(`${this.backendUrl}/api/q-table`);
      if (response.ok) {
        this.qTable = await response.json();
        console.log(`[AI Agent] Q-Table chargée avec succès (${Object.keys(this.qTable).length} états)`);
      } else {
        console.error("[AI Agent] Échec du chargement de la Q-Table depuis l'API");
      }
    } catch (error) {
      console.error("[AI Agent] Erreur lors de la connexion avec le serveur API :", error);
    }
  }

  /**
   * Synchronise les mises à jour locales en attente avec le serveur FastAPI.
   */
  public async syncPendingUpdates(): Promise<void> {
    const keys = Object.keys(this.pendingUpdates);
    if (keys.length === 0) return;

    const payload: Record<string, [number, number]> = {};
    for (const key of keys) {
      payload[key] = this.pendingUpdates[key];
    }

    // Vider les mises à jour en attente avant l'envoi pour éviter les conflits si d'autres se produisent pendant le fetch
    this.pendingUpdates = {};

    try {
      const response = await fetch(`${this.backendUrl}/api/q-table/bulk`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        console.log(`[AI Agent] Synchronisation réussie pour ${keys.length} états.`);
      } else {
        console.error("[AI Agent] Échec de la synchronisation de la Q-Table");
        // En cas d'échec, on remet les clés pour réessayer plus tard
        Object.assign(this.pendingUpdates, payload);
      }
    } catch (error) {
      console.error("[AI Agent] Erreur réseau lors de la synchronisation :", error);
      Object.assign(this.pendingUpdates, payload);
    }
  }

  /**
   * Réinitialise complètement la Q-table locale et serveur.
   */
  public async clearQTable(): Promise<void> {
    this.qTable = {};
    this.pendingUpdates = {};
    try {
      const response = await fetch(`${this.backendUrl}/api/q-table/clear`, {
        method: "DELETE",
      });
      if (response.ok) {
        console.log("[AI Agent] Q-Table réinitialisée sur le serveur.");
      }
    } catch (error) {
      console.error("[AI Agent] Erreur lors de la réinitialisation de la Q-Table :", error);
    }
  }
}
