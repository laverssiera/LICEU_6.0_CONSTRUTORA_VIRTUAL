import jwt from "jsonwebtoken";

export class IdentityRuntime {

  static generateIdentity(payload: any) {

    return jwt.sign(
      payload,
      process.env.JWT_SECRET || "liceu",
      {
        expiresIn: "12h"
      }
    );
  }

  static validateIdentity(token: string) {

    return jwt.verify(
      token,
      process.env.JWT_SECRET || "liceu"
    );
  }

  static trustScore(entity: any) {

    let score = 50;

    if (entity.verified) score += 20;
    if (entity.reputation > 80) score += 20;
    if (entity.ecosystemYears > 5) score += 10;

    return score;
  }
}
