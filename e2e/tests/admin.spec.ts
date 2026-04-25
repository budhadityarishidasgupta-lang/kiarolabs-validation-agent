import { expect, test } from "@playwright/test";

function monitorServerErrors(page, failures: string[]) {
  page.on("response", async (response) => {
    const status = response.status();
    const url = response.url();
    if (status >= 500) {
      failures.push(`${status} ${url}`);
      return;
    }
    if (status === 404 && (url.includes("/admin/") || url.includes("/practice/"))) {
      failures.push(`${status} ${url}`);
    }
  });
}

test("admin control panel loads for admin", async ({ page }) => {
  const failures: string[] = [];
  monitorServerErrors(page, failures);

  await page.goto("/admin");

  await expect(page.getByText("Admin Control Panel")).toBeVisible();
  await expect(page.getByRole("tab", { name: "Comprehension" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Curriculum" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Printable Ingestion" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Manage Printables" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "Students & Access" })).toBeVisible();

  expect.soft(failures, failures.join("\n")).toEqual([]);
});
