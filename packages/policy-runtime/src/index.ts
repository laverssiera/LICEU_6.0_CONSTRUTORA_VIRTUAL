export class SovereignPolicy {

  static evaluate(context: any) {

    if (context.risk > 90) {
      return {
        approved: false,
        reason: "HIGH_RISK"
      };
    }

    if (context.esgViolation) {
      return {
        approved: false,
        reason: "ESG_VIOLATION"
      };
    }

    return {
      approved: true
    };
  }
}
