export type Status =
  "waiting" | "in_progress" | "waiting_for_signoff" | "decided";

export interface ClaimSummary {
  claim_id: string;
  summary: string;
  claim_type: string;
  submitted_on: string;
  amount_claimed: number;
  status: Status;
}

export interface Item {
  description: string;
  category: string;
  amount: number;
}

export interface ClaimDocument {
  name: string;
  type: string;
  content: string;
}

export interface Decision {
  decision: "approve" | "decline" | "refer";
  payout: number;
  reason: string;
  section: string;
  decided_at: string;
}

export interface Payment {
  amount: number;
  handler_id: string | null;
  paid_at: string;
}

export interface Claim extends ClaimSummary {
  policy_id: string;
  customer_id: string;
  incident_date: string;
  incident_location: string;
  story: string;
  items: Item[];
  documents: ClaimDocument[];
  decision: Decision | null;
  payment: Payment | null;
}

export interface Policy {
  policy_id: string;
  plan: string;
  add_ons: string[];
  purchased_on: string;
  sold_through: string;
  trip: {
    destination: string;
    departs_on: string;
    returns_on: string;
    trip_cost: number;
  };
  travelers: string[];
}

export interface PreviousClaim {
  claim_id: string;
  filed_on: string;
  claim_type: string;
  summary: string;
  outcome: string;
  amount_paid: number;
}

export interface Handler {
  handler_id: string;
  name: string;
  role: string;
}

export interface Step {
  step_id: number;
  kind: "model" | "tool_call" | "tool_result";
  text: string;
  created_at: string;
}

async function send<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const body = (await response.json()) as { detail: string };
    throw new Error(body.detail);
  }
  return (await response.json()) as T;
}

function post<T>(path: string, body?: object): Promise<T> {
  return send<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
}

export const api = {
  listClaims: () => send<ClaimSummary[]>("/api/claims"),
  getClaim: (claimId: string) => send<Claim>(`/api/claims/${claimId}`),
  getPolicy: (policyId: string) => send<Policy>(`/api/policies/${policyId}`),
  getClaimHistory: (customerId: string) =>
    send<PreviousClaim[]>(`/api/customers/${customerId}/claims`),
  getInstructions: () => send<{ text: string }>("/api/instructions"),
  listHandlers: () => send<Handler[]>("/api/handlers"),
  listSteps: (claimId: string) => send<Step[]>(`/api/claims/${claimId}/steps`),
  runAgent: (claimId: string) => post<Claim>(`/api/claims/${claimId}/run`),
  signOff: (claimId: string, handlerId: string) =>
    post<Claim>(`/api/claims/${claimId}/sign-off`, { handler_id: handlerId }),
};
