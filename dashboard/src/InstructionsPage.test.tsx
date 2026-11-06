import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { InstructionsPage } from "./InstructionsPage";
import { stubApi } from "./testing";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("shows the instructions with no way to edit them", async () => {
  stubApi({
    "GET /api/instructions": { text: "# The UnderCover Agent\n\nDecide." },
  });
  render(<InstructionsPage />);
  const instructions = await screen.findByLabelText("Instructions");
  expect(instructions.textContent).toBe("# The UnderCover Agent\n\nDecide.");
  expect(screen.queryByRole("textbox")).toBeNull();
  expect(screen.queryByRole("button")).toBeNull();
  expect(instructions.hasAttribute("contenteditable")).toBe(false);
});
