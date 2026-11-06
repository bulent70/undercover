import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ClaimPage } from "./ClaimPage";
import { claim, claimRoutes, decided, stubApi } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the story, items, documents, policy and history", async () => {
  stubApi(claimRoutes(claim));
  render(<ClaimPage claimId="CLM-1001" />);
  expect(
    await screen.findByText("My flight home from Rome was canceled."),
  ).toBeDefined();
  expect(screen.getByText("Airport hotel, one night")).toBeDefined();
  expect(screen.getByText("$245.00")).toBeDefined();
  expect(screen.getByText("$420.00")).toBeDefined();
  expect(screen.getByText("Hotel receipt")).toBeDefined();
  const policy = await screen.findByRole("region", { name: "Policy" });
  expect(within(policy).getByText("Premium")).toBeDefined();
  expect(within(policy).getByText("Electronics plus")).toBeDefined();
  expect(within(policy).getByText("Maya Patel")).toBeDefined();
  const history = await screen.findByRole("region", { name: "Claim history" });
  expect(within(history).getByText("CLM-0412")).toBeDefined();
  expect(screen.queryByRole("region", { name: "Decision" })).toBeNull();
});

it("shows the decision, payout, reason, section and payment", async () => {
  stubApi(claimRoutes(decided));
  render(<ClaimPage claimId="CLM-1001" />);
  const decision = await screen.findByRole("region", { name: "Decision" });
  expect(within(decision).getByText("Approved")).toBeDefined();
  expect(
    within(decision).getByText("$1,250.00", { selector: "h2 span" }),
  ).toBeDefined();
  expect(
    within(decision).getByText(
      "The delay is covered. The costs are within the limit.",
    ),
  ).toBeDefined();
  expect(
    within(decision).getByText("Policy wording: 3. Trip Delay"),
  ).toBeDefined();
  expect(decision.textContent).toContain("with sign-off by HND-01");
});

it("says when there are no previous claims", async () => {
  stubApi({ ...claimRoutes(claim), "GET /api/customers/CUS-3001/claims": [] });
  render(<ClaimPage claimId="CLM-1001" />);
  expect(await screen.findByText("No previous claims.")).toBeDefined();
});

it("says when the claim cannot load", async () => {
  stubApi({});
  render(<ClaimPage claimId="CLM-9999" />);
  expect((await screen.findByRole("alert")).textContent).toContain(
    "GET /api/claims/CLM-9999 not found",
  );
});
