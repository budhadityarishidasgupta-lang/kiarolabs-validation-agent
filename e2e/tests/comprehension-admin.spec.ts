import { expect, test } from "@playwright/test";

test("comprehension admin surface renders upload and passages table", async ({ page }) => {
  await page.goto("/admin");
  await page.getByRole("tab", { name: "Comprehension" }).click();

  await expect(page.getByText("Comprehension Content Management")).toBeVisible();
  await expect(page.getByText("Upload Comprehension CSV")).toBeVisible();
  await expect(page.getByText("Uploaded Passages")).toBeVisible();
});
