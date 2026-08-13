export class CollectiveMind {

  static async deliberate(inputs: any[]) {

    const consensus = {
      confidence: 0,
      recommendation: "",
      participating_monoliths: []
    };

    let total = 0;

    for (const input of inputs) {

      total += input.weight;

      consensus.participating_monoliths.push(
        input.monolith
      );
    }

    consensus.confidence = total / inputs.length;

    if (consensus.confidence > 80) {
      consensus.recommendation = "APPROVE";
    } else {
      consensus.recommendation = "REVIEW";
    }

    return consensus;
  }
}
