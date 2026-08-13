export const EVENT_VERSIONS = [
  "v1",
  "v2",
] as const;

export type EventVersion = (typeof EVENT_VERSIONS)[number];

export const CANONICAL_EVENTS = {
  LEAD_CREATED: "lead.created",
  MATCH_GENERATED: "match.generated",
  DEAL_CLOSED: "deal.closed",
  PROPOSAL_SENT: "proposal.sent",
  CONTRACT_CREATED: "contract.created",
  CONTRACT_SIGNED: "contract.signed",
  COMMISSION_PROTECTED: "commission.protected",
  PAYMENT_GENERATED: "payment.generated",
  CAMPAIGN_TRIGGERED: "campaign.triggered",
} as const;

export type CanonicalEventType = (typeof CANONICAL_EVENTS)[keyof typeof CANONICAL_EVENTS];

export interface EventEnvelope {
  id: string;
  type: CanonicalEventType;
  version: EventVersion;
  source: string;
  timestamp: string;
  payload: Record<string, string>;
}

export const EVENT_CATALOG = [
  {
    enumName: "LEAD_CREATED",
    eventKey: "lead.created",
    versions: ["v1", "v2"] as const,
  },
  {
    enumName: "MATCH_GENERATED",
    eventKey: "match.generated",
    versions: ["v1", "v2"] as const,
  },
  {
    enumName: "DEAL_CLOSED",
    eventKey: "deal.closed",
    versions: ["v1", "v2"] as const,
  },
  {
    enumName: "PROPOSAL_SENT",
    eventKey: "proposal.sent",
    versions: ["v1", "v2"] as const,
  },
  {
    enumName: "CONTRACT_CREATED",
    eventKey: "contract.created",
    versions: ["v1", "v2"] as const,
  },
  {
    enumName: "CONTRACT_SIGNED",
    eventKey: "contract.signed",
    versions: ["v1", "v2"] as const,
  },
  {
    enumName: "COMMISSION_PROTECTED",
    eventKey: "commission.protected",
    versions: ["v1", "v2"] as const,
  },
  {
    enumName: "PAYMENT_GENERATED",
    eventKey: "payment.generated",
    versions: ["v1", "v2"] as const,
  },
  {
    enumName: "CAMPAIGN_TRIGGERED",
    eventKey: "campaign.triggered",
    versions: ["v1", "v2"] as const,
  },
] as const;
