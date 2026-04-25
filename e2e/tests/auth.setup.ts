import { expect, test } from "@playwright/test";

test("admin login setup", async ({ page }) => {
  const email = process.env.E2E_ADMIN_EMAIL;
  const password = process.env.E2E_ADMIN_PASSWORD;

  if (!email || !password) {
    throw new Error("E2E_ADMIN_EMAIL and E2E_ADMIN_PASSWORD must be set");
  }

  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign In" }).click();

  await page.waitForURL(/\/dashboard$/, { timeout: 30000 });
  await expect(page).toHaveURL(/\/dashboard$/);

  await page.context().storageState({ path: ".auth/admin.json" });
});
