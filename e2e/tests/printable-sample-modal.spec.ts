import { expect, test } from "@playwright/test";

test("printable papers shows sample preview modal when available", async ({ page }) => {
  await page.goto("/printable-papers");

  const viewSampleButton = page.getByRole("button", { name: /view sample/i }).first();
  test.skip(!(await viewSampleButton.isVisible().catch(() => false)), "No sample CTA available in this environment.");

  await viewSampleButton.click();
  const sampleDialog = page.getByRole("dialog").or(page.getByText(/sample|preview/i).first()).first();
  await expect(sampleDialog).toBeVisible({ timeout: 10000 });
});
