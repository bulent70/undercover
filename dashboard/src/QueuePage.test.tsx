import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { QueuePage } from "./QueuePage";
import { stubApi, summaries } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("lists the claims with their states and amounts in US dollars", async () => {
  stubApi({ "GET /api/claims": summaries });
  render(<QueuePage />);
  const table = await screen.findByRole("table");
  const rows = within(table).getAllByRole("row");
  expect(rows).toHaveLength(5);
  expect(within(rows[1]).getByText("CLM-1001")).toBeDefined();
  expect(within(rows[1]).getByText("Waiting")).toBeDefined();
  expect(within(rows[1]).getByText("$420.00")).toBeDefined();
  expect(within(rows[1]).getByText("Trip delay")).toBeDefined();
  expect(within(rows[2]).getByText("In progress")).toBeDefined();
  expect(within(rows[2]).getByText("$1,150.00")).toBeDefined();
  expect(within(rows[3]).getByText("Waiting for sign-off")).toBeDefined();
  expect(within(rows[3]).getByText("$3,800.00")).toBeDefined();
  expect(within(rows[4]).getByText("Decided")).toBeDefined();
});

it("counts the claims in each state", async () => {
  stubApi({ "GET /api/claims": summaries });
  render(<QueuePage />);
  const tiles = await screen.findByRole("list", { name: "Claims by state" });
  expect(within(tiles).getAllByText("1")).toHaveLength(4);
});

it("says when the queue cannot load", async () => {
  stubApi({});
  render(<QueuePage />);
  expect((await screen.findByRole("alert")).textContent).toContain(
    "Could not load the queue",
  );
});
