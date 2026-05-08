import { expect, test } from "@playwright/test";

test("curriculum admin renders module tabs and overview", async ({ page }) => {
  await page.goto("/admin");
  await page.getByRole("tab", { name: "Curriculum" }).click();

  await expect(page.getByRole("tab", { name: "Maths" })).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("tab", { name: "Spelling" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Words" })).toBeVisible();
  await page.getByRole("tab", { name: "Maths" }).click();

  const activeMathsPanel = page.getByRole("tabpanel").filter({
    has: page.getByText("Maths structure"),
  }).first();

  await expect(activeMathsPanel.getByText("Maths structure")).toBeVisible({ timeout: 15000 });
  await expect(
    activeMathsPanel
      .getByText("Select a lesson to view its details.")
      .or(activeMathsPanel.getByText("Lesson Content"))
      .first(),
  ).toBeVisible({ timeout: 15000 });
});
