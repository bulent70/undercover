import { expect, test } from "@playwright/test";
import { backendUrl } from "../playwright.config";

test("the queue lists 25 claims and a claim opens", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Claims queue" }),
  ).toBeVisible();
  await expect(page.getByRole("row")).toHaveCount(26);

  await page.getByRole("link", { name: "CLM-1001" }).click();
  await expect(page).toHaveURL(/#\/claims\/CLM-1001$/);
  await expect(page.getByText("My flight home from Rome")).toBeVisible();
  await expect(page.getByRole("region", { name: "Policy" })).toBeVisible();
});

test("a payout over $1,000 waits for sign-off, then is paid", async ({
  page,
  request,
}) => {
  const claim = `${backendUrl}/api/claims/CLM-1003`;
  expect((await request.post(`${claim}/start`)).ok()).toBe(true);
  const decided = await request.post(`${claim}/decision`, {
    data: {
      decision: "approve",
      payout: 1250,
      reason: "The medical costs are covered.",
      section: "7. Emergency Medical",
    },
  });
  expect(decided.ok()).toBe(true);

  await page.goto("/#/claims/CLM-1003");
  await expect(page.getByText("Waiting for sign-off").first()).toBeVisible();
  const signOff = page.getByRole("region", { name: "Sign-off" });
  await signOff.getByLabel("Handler").selectOption({ label: "Dana Whitfield" });
  await signOff.getByRole("button", { name: "Sign off and pay" }).click();

  const decision = page.getByRole("region", { name: "Decision" });
  await expect(decision).toContainText("Paid $1,250.00");
  await expect(decision).toContainText("with sign-off by HND-01");
  await expect(page.getByText("Decided", { exact: true })).toBeVisible();
});
