const memory = new Map();

export class EcosystemMemory {

  static remember(key: string, value: any) {

    memory.set(key, {
      timestamp: Date.now(),
      value
    });
  }

  static recall(key: string) {

    return memory.get(key);
  }

  static snapshot() {

    return Array.from(memory.entries());
  }
}
