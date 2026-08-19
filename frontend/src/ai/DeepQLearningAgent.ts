class SimpleMLP {
  public weights1: number[][]; // [inputSize][hidden1]
  public bias1: number[];      // [hidden1]
  public weights2: number[][]; // [hidden1][hidden2]
  public bias2: number[];      // [hidden2]
  public weights3: number[][]; // [hidden2][outputSize]
  public bias3: number[];      // [outputSize]

  // Velocities for Momentum SGD
  private vW1: number[][];
  private vb1: number[];
  private vW2: number[][];
  private vb2: number[];
  private vW3: number[][];
  private vb3: number[];

  private learningRate = 0.01;
  private momentum = 0.9;

  constructor(inputSize = 7, hidden1 = 24, hidden2 = 24, outputSize = 2) {
    this.weights1 = this.initHe(inputSize, hidden1);
    this.bias1 = new Array(hidden1).fill(0.0);
    this.weights2 = this.initHe(hidden1, hidden2);
    this.bias2 = new Array(hidden2).fill(0.0);
    this.weights3 = this.initHe(hidden2, outputSize);
    this.bias3 = new Array(outputSize).fill(0.0);

    this.vW1 = this.initZeros(inputSize, hidden1);
    this.vb1 = new Array(hidden1).fill(0.0);
    this.vW2 = this.initZeros(hidden1, hidden2);
    this.vb2 = new Array(hidden2).fill(0.0);
    this.vW3 = this.initZeros(hidden2, outputSize);
    this.vb3 = new Array(outputSize).fill(0.0);
  }

  private initHe(rows: number, cols: number): number[][] {
    const scale = Math.sqrt(2.0 / rows);
    const mat: number[][] = [];
    for (let r = 0; r < rows; r++) {
      const row: number[] = [];
      for (let c = 0; c < cols; c++) {
        // Box-Muller transform
        const u1 = Math.random() || 0.0001;
        const u2 = Math.random();
        const randStdNormal = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
        row.push(randStdNormal * scale);
      }
      mat.push(row);
    }
    return mat;
  }

  private initZeros(rows: number, cols: number): number[][] {
    return Array.from({ length: rows }, () => new Array(cols).fill(0.0));
  }

  // Forward pass
  public forward(x: number[]): {
    h1_z: number[];
    h1_a: number[];
    h2_z: number[];
    h2_a: number[];
    y: number[];
  } {
    // Hidden Layer 1
    const h1_z = [...this.bias1];
    for (let j = 0; j < h1_z.length; j++) {
      for (let i = 0; i < x.length; i++) {
        h1_z[j] += x[i] * this.weights1[i][j];
      }
    }
    const h1_a = h1_z.map(v => Math.max(0, v)); // ReLU

    // Hidden Layer 2
    const h2_z = [...this.bias2];
    for (let j = 0; j < h2_z.length; j++) {
      for (let i = 0; i < h1_a.length; i++) {
        h2_z[j] += h1_a[i] * this.weights2[i][j];
      }
    }
    const h2_a = h2_z.map(v => Math.max(0, v)); // ReLU

    // Output Layer (Linear values)
    const y = [...this.bias3];
    for (let j = 0; j < y.length; j++) {
      for (let i = 0; i < h2_a.length; i++) {
        y[j] += h2_a[i] * this.weights3[i][j];
      }
    }

    return { h1_z, h1_a, h2_z, h2_a, y };
  }

  // Backward pass and gradient update
  public trainStep(x: number[], action: number, targetVal: number): number {
    const { h1_z, h1_a, h2_z, h2_a, y } = this.forward(x);

    // Compute error and loss
    const error = y[action] - targetVal;
    const loss = 0.5 * error * error;

    // Output Layer backpropagation
    const dy = [0.0, 0.0];
    dy[action] = error;

    const dW3 = this.initZeros(this.weights3.length, this.weights3[0].length);
    const db3 = [...dy];
    for (let i = 0; i < h2_a.length; i++) {
      for (let j = 0; j < dy.length; j++) {
        dW3[i][j] = h2_a[i] * dy[j];
      }
    }

    // Hidden Layer 2 backpropagation
    const dh2 = new Array(h2_a.length).fill(0.0);
    for (let i = 0; i < h2_a.length; i++) {
      for (let j = 0; j < dy.length; j++) {
        dh2[i] += dy[j] * this.weights3[i][j];
      }
    }
    const dz2 = new Array(h2_z.length).fill(0.0);
    for (let i = 0; i < h2_z.length; i++) {
      dz2[i] = h2_z[i] > 0 ? dh2[i] : 0.0; // ReLU derivative
    }

    const dW2 = this.initZeros(this.weights2.length, this.weights2[0].length);
    const db2 = [...dz2];
    for (let i = 0; i < h1_a.length; i++) {
      for (let j = 0; j < dz2.length; j++) {
        dW2[i][j] = h1_a[i] * dz2[j];
      }
    }

    // Hidden Layer 1 backpropagation
    const dh1 = new Array(h1_a.length).fill(0.0);
    for (let i = 0; i < h1_a.length; i++) {
      for (let j = 0; j < dz2.length; j++) {
        dh1[i] += dz2[j] * this.weights2[i][j];
      }
    }
    const dz1 = new Array(h1_z.length).fill(0.0);
    for (let i = 0; i < h1_z.length; i++) {
      dz1[i] = h1_z[i] > 0 ? dh1[i] : 0.0; // ReLU derivative
    }

    const dW1 = this.initZeros(this.weights1.length, this.weights1[0].length);
    const db1 = [...dz1];
    for (let i = 0; i < x.length; i++) {
      for (let j = 0; j < dz1.length; j++) {
        dW1[i][j] = x[i] * dz1[j];
      }
    }

    // Update weights & biases using SGD with Momentum
    this.updateWeights(this.weights1, dW1, this.vW1);
    this.updateBiases(this.bias1, db1, this.vb1);
    this.updateWeights(this.weights2, dW2, this.vW2);
    this.updateBiases(this.bias2, db2, this.vb2);
    this.updateWeights(this.weights3, dW3, this.vW3);
    this.updateBiases(this.bias3, db3, this.vb3);

    return loss;
  }

  private updateWeights(W: number[][], dW: number[][], vW: number[][]) {
    for (let r = 0; r < W.length; r++) {
      for (let c = 0; c < W[0].length; c++) {
        const grad = Math.max(-5.0, Math.min(5.0, dW[r][c])); // Gradient clipping
        vW[r][c] = this.momentum * vW[r][c] + (1 - this.momentum) * grad;
        W[r][c] -= this.learningRate * vW[r][c];
      }
    }
  }

  private updateBiases(b: number[], db: number[], vb: number[]) {
    for (let i = 0; i < b.length; i++) {
      const grad = Math.max(-5.0, Math.min(5.0, db[i])); // Gradient clipping
      vb[i] = this.momentum * vb[i] + (1 - this.momentum) * grad;
      b[i] -= this.learningRate * vb[i];
    }
  }

  public softUpdateFrom(other: SimpleMLP, tau = 0.01) {
    const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

    for (let r = 0; r < this.weights1.length; r++) {
      for (let c = 0; c < this.weights1[0].length; c++) {
        this.weights1[r][c] = lerp(this.weights1[r][c], other.weights1[r][c], tau);
      }
    }
    for (let i = 0; i < this.bias1.length; i++) {
      this.bias1[i] = lerp(this.bias1[i], other.bias1[i], tau);
    }

    for (let r = 0; r < this.weights2.length; r++) {
      for (let c = 0; c < this.weights2[0].length; c++) {
        this.weights2[r][c] = lerp(this.weights2[r][c], other.weights2[r][c], tau);
      }
    }
    for (let i = 0; i < this.bias2.length; i++) {
      this.bias2[i] = lerp(this.bias2[i], other.bias2[i], tau);
    }

    for (let r = 0; r < this.weights3.length; r++) {
      for (let c = 0; c < this.weights3[0].length; c++) {
        this.weights3[r][c] = lerp(this.weights3[r][c], other.weights3[r][c], tau);
      }
    }
    for (let i = 0; i < this.bias3.length; i++) {
      this.bias3[i] = lerp(this.bias3[i], other.bias3[i], tau);
    }
  }

  public copyFrom(other: SimpleMLP) {
    this.softUpdateFrom(other, 1.0);
  }

  public getWeightsJSON(): string {
    return JSON.stringify({
      w1: this.weights1,
      b1: this.bias1,
      w2: this.weights2,
      b2: this.bias2,
      w3: this.weights3,
      b3: this.bias3
    });
  }

  public setWeightsFromJSON(jsonStr: string) {
    const data = JSON.parse(jsonStr);
    if (data.w1) this.weights1 = data.w1;
    if (data.b1) this.bias1 = data.b1;
    if (data.w2) this.weights2 = data.w2;
    if (data.b2) this.bias2 = data.b2;
    if (data.w3) this.weights3 = data.w3;
    if (data.b3) this.bias3 = data.b3;
  }
}

interface Transition {
  state: number[];
  action: number;
  reward: number;
  nextState: number[];
  done: boolean;
}

export class DeepQLearningAgent {
  public policyNet: SimpleMLP;
  public targetNet: SimpleMLP;
  
  // Replay memory
  private replayBuffer: Transition[] = [];
  private bufferCapacity = 2000;
  private batchSize = 32;

  // Hyperparameters
  private gamma = 0.95;
  public epsilon = 1.0;
  private epsilonDecay = 0.9995;
  private epsilonMin = 0.05;

  // Metrics
  public lastLoss = 0.0;
  public totalSteps = 0;
  
  // Interface Compatibility
  public qTable: Record<string, [number, number]> = {};
  private evaluatedStates: Set<string> = new Set();
  
  private actions = [0, 1];
  private backendUrl: string;

  constructor(
    actions: number[] = [0, 1],
    backendUrl = "http://localhost:8000"
  ) {
    this.actions = actions;
    this.backendUrl = backendUrl;
    this.policyNet = new SimpleMLP(7, 24, 24, 2);
    this.targetNet = new SimpleMLP(7, 24, 24, 2);
    this.targetNet.copyFrom(this.policyNet);
  }

  /**
   * Helper to normalize discrete components to state vector [7]
   */
  public getStateVector(
    nCount: number,
    sCount: number,
    eCount: number,
    oCount: number,
    currentPhase: string,
    timeInPhase: number
  ): number[] {
    const pA = currentPhase === "A" ? 1.0 : 0.0;
    const pB = currentPhase === "B" ? 1.0 : 0.0;
    const normTime = Math.min(1.0, timeInPhase / 600.0); // Normalisé par rapport à MAX_GREEN_TIME
    
    return [
      nCount / 10.0, // Normalisé par rapport à une file max typique
      sCount / 10.0,
      eCount / 10.0,
      oCount / 10.0,
      pA,
      pB,
      normTime
    ];
  }

  /**
   * String representation of state vector for compatibility with UI Heatmap
   */
  public getStateKey(
    nCount: number,
    sCount: number,
    eCount: number,
    oCount: number,
    currentPhase: string,
    timeInPhase: number
  ): string {
    // Simple discretization bucket for dictionary compatibility
    const discretize = (count: number): number => {
      if (count === 0) return 0;
      if (count <= 2) return 1;
      if (count <= 5) return 2;
      return 3;
    };
    const timeDisc = Math.floor(timeInPhase / 20);
    return `${discretize(nCount)}_${discretize(sCount)}_${discretize(eCount)}_${discretize(oCount)}_${currentPhase}_${timeDisc}`;
  }

  /**
   * Selects action using epsilon-greedy strategy
   */
  public chooseAction(stateVector: number[]): number {
    this.totalSteps++;
    
    // Decay epsilon
    if (this.epsilon > this.epsilonMin) {
      this.epsilon *= this.epsilonDecay;
    }

    if (Math.random() < this.epsilon) {
      return Math.floor(Math.random() * this.actions.length);
    }

    // Inference
    const { y } = this.policyNet.forward(stateVector);
    return y[0] >= y[1] ? 0 : 1;
  }

  /**
   * Stores transition in Replay Buffer and runs one train step if batch is available
   */
  public learn(
    stateVector: number[],
    action: number,
    reward: number,
    nextStateVector: number[],
    stateKey?: string
  ): void {
    // Save to Replay Buffer
    const transition: Transition = {
      state: stateVector,
      action,
      reward,
      nextState: nextStateVector,
      done: false
    };

    this.replayBuffer.push(transition);
    if (this.replayBuffer.length > this.bufferCapacity) {
      this.replayBuffer.shift();
    }

    // Update evaluated states cache for UI rendering
    if (stateKey) {
      this.evaluatedStates.add(stateKey);
      this.updateQTableCache(stateKey, stateVector);
    }

    // Train DQN with a sampled mini-batch
    if (this.replayBuffer.length >= this.batchSize) {
      this.trainBatch();
    }
  }

  /**
   * Recalculates and caches Q-values for visual elements (Heatmap/PieChart)
   */
  private updateQTableCache(stateKey: string, stateVector: number[]) {
    const { y } = this.policyNet.forward(stateVector);
    this.qTable[stateKey] = [y[0], y[1]];
  }

  /**
   * Refreshes the entire Q-Table cache for all previously observed states
   */
  public refreshQTableCache() {
    for (const key of this.evaluatedStates) {
      // Parse key: e.g. "1_0_2_1_A_4" -> back to rough representation for model evaluation
      const parts = key.split('_');
      if (parts.length >= 6) {
        const nCount = parseInt(parts[0]) * 3; // rough center values for buckets
        const sCount = parseInt(parts[1]) * 3;
        const eCount = parseInt(parts[2]) * 3;
        const oCount = parseInt(parts[3]) * 3;
        const currentPhase = parts[4];
        const timeInPhase = parseInt(parts[5]) * 20;

        const vec = this.getStateVector(nCount, sCount, eCount, oCount, currentPhase, timeInPhase);
        const { y } = this.policyNet.forward(vec);
        this.qTable[key] = [y[0], y[1]];
      }
    }
  }

  /**
   * Train step on a random batch from Replay Buffer
   */
  private trainBatch() {
    let totalLoss = 0.0;

    for (let step = 0; step < 4; step++) { // 4 batch updates per learning call
      // Sample batch
      const batch: Transition[] = [];
      for (let i = 0; i < this.batchSize; i++) {
        const randIdx = Math.floor(Math.random() * this.replayBuffer.length);
        batch.push(this.replayBuffer[randIdx]);
      }

      for (const t of batch) {
        // Calculate Target Q-value using target network
        const targetNetOutputs = this.targetNet.forward(t.nextState).y;
        const maxNextQ = Math.max(...targetNetOutputs);
        
        const targetQ = t.reward + this.gamma * maxNextQ;
        
        // Train policyNet on this experience transition
        const loss = this.policyNet.trainStep(t.state, t.action, targetQ);
        totalLoss += loss;
      }
    }

    this.lastLoss = totalLoss / (this.batchSize * 4);

    // Soft update target network: target = target * 0.99 + policy * 0.01
    this.targetNet.softUpdateFrom(this.policyNet, 0.01);
  }

  public getBufferSize(): number {
    return this.replayBuffer.length;
  }

  /**
   * Save network weights to backend PostgreSQL database
   */
  public async syncPendingUpdates(): Promise<void> {
    try {
      const weightsJSON = this.policyNet.getWeightsJSON();
      const response = await fetch(`${this.backendUrl}/api/dqn-weights`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          key: "latest",
          weights_json: weightsJSON
        }),
      });

      if (response.ok) {
        console.log("[DQN Agent] Poids synchronisés avec succès dans la base de données PostgreSQL.");
      } else {
        console.error("[DQN Agent] Échec de la synchronisation des poids.");
      }
    } catch (error) {
      console.error("[DQN Agent] Erreur réseau lors de la synchronisation des poids :", error);
    }
  }

  /**
   * Load network weights from backend database
   */
  public async loadQTable(): Promise<void> {
    try {
      const response = await fetch(`${this.backendUrl}/api/dqn-weights`);
      if (response.ok) {
        const data = await response.json();
        if (data && data.weights_json) {
          this.policyNet.setWeightsFromJSON(data.weights_json);
          this.targetNet.copyFrom(this.policyNet);
          console.log("[DQN Agent] Réseau de neurones chargé avec succès depuis PostgreSQL.");
          
          // Prepopulate some default states in the cache to make sure UI is populated
          this.prepopulateCache();
        }
      } else {
        console.log("[DQN Agent] Aucun poids DQN trouvé sur le serveur. Initialisation d'un nouveau réseau.");
        this.prepopulateCache();
      }
    } catch (error) {
      console.error("[DQN Agent] Erreur lors du chargement des poids DQN :", error);
      this.prepopulateCache();
    }
  }

  /**
   * Clear network weights and database entries
   */
  public async clearQTable(): Promise<void> {
    this.policyNet = new SimpleMLP(7, 24, 24, 2);
    this.targetNet.copyFrom(this.policyNet);
    this.replayBuffer = [];
    this.epsilon = 1.0;
    this.lastLoss = 0.0;
    this.totalSteps = 0;
    this.qTable = {};
    this.evaluatedStates.clear();

    try {
      const response = await fetch(`${this.backendUrl}/api/dqn-weights/clear`, {
        method: "DELETE",
      });
      if (response.ok) {
        console.log("[DQN Agent] Poids réinitialisés sur le serveur.");
        this.prepopulateCache();
      }
    } catch (error) {
      console.error("[DQN Agent] Erreur lors de la réinitialisation sur le serveur :", error);
    }
  }

  /**
   * Pre-populates the cache with some standard states so the Heatmap starts with beautiful content
   */
  private prepopulateCache() {
    const phases = ["A", "B"];
    // Add common queue counts
    const testCases = [
      [0, 0, 0, 0], // Empty
      [2, 2, 0, 0], // Small queues North-South
      [0, 0, 2, 2], // Small queues East-West
      [4, 4, 1, 1], // Heavy queues North-South
      [1, 1, 4, 4], // Heavy queues East-West
      [3, 3, 3, 3], // Medium queues everywhere
      [6, 6, 2, 2], // Very heavy North-South
      [2, 2, 6, 6], // Very heavy East-West
    ];

    for (const phase of phases) {
      for (const counts of testCases) {
        for (const time of [100, 300, 500]) {
          const key = this.getStateKey(counts[0], counts[1], counts[2], counts[3], phase, time);
          const vec = this.getStateVector(counts[0], counts[1], counts[2], counts[3], phase, time);
          this.evaluatedStates.add(key);
          this.updateQTableCache(key, vec);
        }
      }
    }
  }
}
