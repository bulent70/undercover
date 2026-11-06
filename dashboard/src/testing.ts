import { vi } from "vitest";
import type {
  Claim,
  ClaimSummary,
  Decision,
  Payment,
  Policy,
  PreviousClaim,
} from "./api";

export type Routes = Record<string, unknown>;

export function stubApi(routes: Routes) {
  const fetchStub = vi.fn((input: string, init?: RequestInit) => {
    const key = `${init?.method ?? "GET"} ${input}`;
    if (!(key in routes)) {
      return Promise.resolve(
        new Response(JSON.stringify({ detail: `${key} not found` }), {
          status: 404,
        }),
      );
    }
    const route = routes[key];
    const body =
      typeof route === "function" ? (route as () => unknown)() : route;
    return Promise.resolve(new Response(JSON.stringify(body)));
  });
  vi.stubGlobal("fetch", fetchStub);
  return fetchStub;
}

export const summaries: ClaimSummary[] = [
  {
    claim_id: "CLM-1001",
    summary: "Flight home canceled by the airline",
    claim_type: "trip_delay",
    submitted_on: "2026-06-24",
    amount_claimed: 420,
    status: "waiting",
    decision: null,
    payout: null,
  },
  {
    claim_id: "CLM-1002",
    summary: "Bag lost on the way to Tokyo",
    claim_type: "baggage",
    submitted_on: "2026-06-25",
    amount_claimed: 1150,
    status: "in_progress",
    decision: null,
    payout: null,
  },
  {
    claim_id: "CLM-1003",
    summary: "Trip canceled after a hospital stay",
    claim_type: "trip_cancellation",
    submitted_on: "2026-06-26",
    amount_claimed: 3800,
    status: "waiting_for_signoff",
    decision: "approve",
    payout: 1250,
  },
  {
    claim_id: "CLM-1004",
    summary: "Passport stolen in Lisbon",
    claim_type: "passport",
    submitted_on: "2026-06-27",
    amount_claimed: 186,
    status: "decided",
    decision: "decline",
    payout: 0,
  },
];

export const claim: Claim = {
  ...summaries[0],
  policy_id: "POL-2001",
  customer_id: "CUS-3001",
  incident_date: "2026-06-18",
  incident_location: "Rome, Italy",
  story: "My flight home from Rome was canceled.",
  items: [
    {
      description: "Airport hotel, one night",
      category: "accommodation",
      amount: 245,
    },
    { description: "Dinner and breakfast", category: "meals", amount: 95 },
    { description: "Taxis", category: "transport", amount: 80 },
  ],
  documents: [
    {
      name: "Hotel receipt",
      type: "receipt",
      content: "Hotel Aurelia Fiumicino. Total paid: $245.00.",
    },
  ],
  decision: null,
  payment: null,
};

export const decision: Decision = {
  decision: "approve",
  payout: 1250,
  reason: "The delay is covered. The costs are within the limit.",
  section: "3. Trip Delay",
  decided_at: "2026-11-06T10:00:00+00:00",
};

export const payment: Payment = {
  amount: 1250,
  handler_id: "HND-01",
  paid_at: "2026-11-06T11:00:00+00:00",
};

export const decided: Claim = {
  ...claim,
  status: "decided",
  decision,
  payment,
};

export const policy: Policy = {
  policy_id: "POL-2001",
  plan: "premium",
  add_ons: ["electronics_plus"],
  purchased_on: "2026-04-22",
  sold_through: "Meridian Air checkout",
  trip: {
    destination: "Rome, Italy",
    departs_on: "2026-06-10",
    returns_on: "2026-06-18",
    trip_cost: 3100,
  },
  travelers: ["Maya Patel"],
};

export const history: PreviousClaim[] = [
  {
    claim_id: "CLM-0412",
    filed_on: "2024-08-19",
    claim_type: "baggage_delay",
    summary: "Checked bag arrived 30 hours late in Lisbon",
    outcome: "approved",
    amount_paid: 140,
  },
];

export function claimRoutes(current: Claim | (() => Claim)): Routes {
  return {
    "GET /api/claims/CLM-1001": current,
    "GET /api/policies/POL-2001": policy,
    "GET /api/customers/CUS-3001/claims": history,
    "GET /api/claims/CLM-1001/steps": [],
    "GET /api/handlers": [
      { handler_id: "HND-01", name: "Dana Whitfield", role: "Senior" },
      { handler_id: "HND-02", name: "Marcus Oyelaran", role: "Handler" },
    ],
  };
}
