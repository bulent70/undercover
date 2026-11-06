import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";
import { claimRoutes, claim, stubApi, summaries } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.location.hash = "";
});

it("shows the queue by default", async () => {
  stubApi({ "GET /api/claims": summaries });
  render(<App />);
  expect(
    await screen.findByRole("heading", { name: "Claims queue" }),
  ).toBeDefined();
});

it("follows the hash to a claim and to the instructions", async () => {
  stubApi({
    ...claimRoutes(claim),
    "GET /api/claims": summaries,
    "GET /api/instructions": { text: "# The UnderCover Agent" },
  });
  render(<App />);
  await screen.findByRole("heading", { name: "Claims queue" });

  act(() => {
    window.location.hash = "#/claims/CLM-1001";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  });
  expect(
    await screen.findByText("My flight home from Rome was canceled."),
  ).toBeDefined();

  act(() => {
    window.location.hash = "#/instructions";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  });
  expect(await screen.findByText("# The UnderCover Agent")).toBeDefined();
});
