import { expect, test } from "@playwright/test";

test("curriculum admin renders module tabs and overview", async ({ page }) => {
  await page.goto("/admin");
  await page.getByRole("tab", { name: "Curriculum" }).click();

  await expect(page.getByText("Curriculum Management")).toBeVisible();
  await expect(page.getByRole("tab", { name: "Maths" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Spelling" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Words" })).toBeVisible();

  await expect(page.getByText("Maths").first()).toBeVisible();
  await expect(page.getByText("Spelling").first()).toBeVisible();
  await expect(page.getByText("Words").first()).toBeVisible();
});
