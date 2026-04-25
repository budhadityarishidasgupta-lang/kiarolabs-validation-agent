import { expect, test } from "@playwright/test";

test("curriculum admin renders module tabs and overview", async ({ page }) => {
  await page.goto("/admin");
  await page.getByRole("tab", { name: "Curriculum" }).click();

  await expect(page.getByRole("tab", { name: "Maths" })).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("tab", { name: "Spelling" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Words" })).toBeVisible();

  await expect(
    page
      .getByText("Curriculum Management")
      .or(page.getByText("Create Lesson"))
      .or(page.getByText("Current Lessons")),
  ).toBeVisible();
});
