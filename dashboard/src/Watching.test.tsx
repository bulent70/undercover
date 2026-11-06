import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import type { Claim, Step } from "./api";
import { ClaimPage } from "./ClaimPage";
import { QueuePage } from "./QueuePage";
import {
  claim,
  claimRoutes,
  decided,
  decision,
  payment,
  stubApi,
  summaries,
} from "./testing";

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const inProgress: Claim = { ...claim, status: "in_progress" };
const waitingForSignOff: Claim = {
  ...claim,
  status: "waiting_for_signoff",
  decision: { ...decision, payout: 1250 },
};

function step(stepId: number, kind: Step["kind"], text: string): Step {
  return { step_id: stepId, kind, text, created_at: "2026-11-06T10:00:00" };
}

function stepCalls(fetchStub: ReturnType<typeof stubApi>) {
  return fetchStub.mock.calls.filter(([path]) => path.endsWith("/steps"))
    .length;
}

it("shows steps as they arrive and stops polling once decided", async () => {
  const claims = [inProgress, inProgress, decided];
  const steps = [
    [step(1, "tool_call", 'get_claim {"claim_id": "CLM-1001"}')],
    [
      step(1, "tool_call", 'get_claim {"claim_id": "CLM-1001"}'),
      step(2, "tool_result", `get_claim: ${"x".repeat(500)}`),
    ],
    [
      step(1, "tool_call", 'get_claim {"claim_id": "CLM-1001"}'),
      step(2, "tool_result", `get_claim: ${"x".repeat(500)}`),
      step(3, "model", "Approved and paid."),
    ],
  ];
  const fetchStub = stubApi({
    ...claimRoutes(() => claims.shift() ?? decided),
    "GET /api/claims/CLM-1001/steps": () => steps.shift() ?? [],
  });
  render(<ClaimPage claimId="CLM-1001" />);

  const panel = await screen.findByRole("region", { name: "Agent steps" });
  expect(
    within(panel).getByText("The agent is working on this claim."),
  ).toBeDefined();
  expect(within(panel).getAllByRole("listitem")).toHaveLength(1);

  await act(() => vi.advanceTimersByTimeAsync(2000));
  expect(within(panel).getAllByRole("listitem")).toHaveLength(2);
  expect(within(panel).getByText(/x…$/)).toBeDefined();

  await act(() => vi.advanceTimersByTimeAsync(2000));
  expect(await screen.findByText("Approved and paid.")).toBeDefined();
  expect(screen.getByRole("region", { name: "Decision" })).toBeDefined();

  const callsWhenDecided = stepCalls(fetchStub);
  await act(() => vi.advanceTimersByTimeAsync(6000));
  expect(stepCalls(fetchStub)).toBe(callsWhenDecided);
});

it("runs the agent on a waiting claim", async () => {
  const fetchStub = stubApi({
    ...claimRoutes(claim),
    "POST /api/claims/CLM-1001/run": inProgress,
  });
  render(<ClaimPage claimId="CLM-1001" />);
  fireEvent.click(await screen.findByRole("button", { name: "Run agent" }));
  expect(await screen.findByText("In progress")).toBeDefined();
  expect(screen.queryByRole("button", { name: "Run agent" })).toBeNull();
  expect(
    fetchStub.mock.calls.some(
      ([path, init]) =>
        path === "/api/claims/CLM-1001/run" && init?.method === "POST",
    ),
  ).toBe(true);
});

it("says when the agent cannot start", async () => {
  stubApi(claimRoutes(claim));
  render(<ClaimPage claimId="CLM-1001" />);
  fireEvent.click(await screen.findByRole("button", { name: "Run agent" }));
  expect((await screen.findByRole("alert")).textContent).toContain("not found");
});

it("signs off as the chosen handler and shows the payment", async () => {
  const fetchStub = stubApi({
    ...claimRoutes(waitingForSignOff),
    "POST /api/claims/CLM-1001/sign-off": {
      ...decided,
      payment: { ...payment, handler_id: "HND-02" },
    },
  });
  render(<ClaimPage claimId="CLM-1001" />);
  const panel = await screen.findByRole("region", { name: "Sign-off" });
  expect(screen.queryByRole("button", { name: "Run agent" })).toBeNull();
  await within(panel).findByRole("option", { name: "Marcus Oyelaran" });
  fireEvent.change(within(panel).getByLabelText("Handler"), {
    target: { value: "HND-02" },
  });
  fireEvent.click(
    within(panel).getByRole("button", { name: "Sign off and pay" }),
  );

  const decisionPanel = await screen.findByRole("region", { name: "Decision" });
  expect(decisionPanel.textContent).toContain("Paid $1,250.00");
  expect(decisionPanel.textContent).toContain("with sign-off by HND-02");
  expect(screen.queryByRole("region", { name: "Sign-off" })).toBeNull();
  const signOff = fetchStub.mock.calls.find(([path]) =>
    path.endsWith("/sign-off"),
  );
  expect(signOff?.[1]?.body).toBe(JSON.stringify({ handler_id: "HND-02" }));
});

it("says when a sign-off is refused", async () => {
  stubApi(claimRoutes(waitingForSignOff));
  render(<ClaimPage claimId="CLM-1001" />);
  const panel = await screen.findByRole("region", { name: "Sign-off" });
  await within(panel).findByRole("option", { name: "Dana Whitfield" });
  fireEvent.click(
    within(panel).getByRole("button", { name: "Sign off and pay" }),
  );
  expect((await within(panel).findByRole("alert")).textContent).toContain(
    "not found",
  );
});

it("refreshes the queue while a claim is in progress", async () => {
  const queues = [
    summaries,
    summaries.map((row) => ({ ...row, status: "decided" })),
  ];
  const fetchStub = stubApi({ "GET /api/claims": () => queues.shift() ?? [] });
  render(<QueuePage />);
  const tiles = await screen.findByRole("list", { name: "Claims by state" });
  expect(within(tiles).getAllByText("1")).toHaveLength(4);

  await act(() => vi.advanceTimersByTimeAsync(2000));
  expect(await within(tiles).findByText("4")).toBeDefined();
  const calls = fetchStub.mock.calls.length;
  await act(() => vi.advanceTimersByTimeAsync(6000));
  expect(fetchStub.mock.calls).toHaveLength(calls);
});
