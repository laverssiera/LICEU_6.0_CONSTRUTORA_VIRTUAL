import { connect, NatsConnection } from "nats";
import { randomUUID } from "crypto";

export class FederationSDK {

  private nc!: NatsConnection;

  async connect() {
    this.nc = await connect({
      servers: process.env.NATS_URL || "nats://localhost:4222"
    });

    console.log("Federation Runtime Connected");
  }

  async publish(subject: string, payload: any) {

    const envelope = {
      id: randomUUID(),
      timestamp: new Date().toISOString(),
      source: process.env.MONOLITH_ID,
      tenant: process.env.TENANT_ID || "global",
      trace_id: randomUUID(),
      payload
    };

    this.nc.publish(
      subject,
      Buffer.from(JSON.stringify(envelope))
    );
  }

  async subscribe(subject: string, handler: any) {

    const sub = this.nc.subscribe(subject);

    for await (const msg of sub) {

      const data = JSON.parse(msg.data.toString());

      await handler(data);
    }
  }
}
