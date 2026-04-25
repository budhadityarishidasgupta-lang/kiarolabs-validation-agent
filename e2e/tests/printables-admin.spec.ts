import { expect, test } from "@playwright/test";

test("manage printables tab loads and inspects a paper", async ({ page }) => {
  const failures: string[] = [];

  page.on("response", async (response) => {
    const status = response.status();
    const url = response.url();
    if ((url.includes("/admin/") || url.includes("/practice/")) && status >= 500) {
      failures.push(`${status} ${url}`);
    }
  });

  await page.goto("/admin");
  await page.getByRole("tab", { name: "Manage Printables" }).click();

  await expect(page.getByText("Manage Printable Papers")).toBeVisible();

  const emptyState = page.getByText("No papers found");
  if (await emptyState.isVisible().catch(() => false)) {
    expect.soft(failures, failures.join("\n")).toEqual([]);
    return;
  }

  await page.getByRole("combobox").click();
  const firstOption = page.getByRole("option").first();
  await expect(firstOption).toBeVisible({ timeout: 10000 });
  await firstOption.click();

  await expect(
    page
      .getByText(/Questions|Answers|Status/)
      .or(page.getByText(/Ready for student submission|Answer key has not been saved yet|Answer key incomplete/))
      .first(),
  ).toBeVisible({ timeout: 15000 });

  const viewQuestionsButton = page.getByRole("button", { name: /view questions/i });
  if (await viewQuestionsButton.isEnabled().catch(() => false)) {
    await viewQuestionsButton.click();
    await expect(
      page
        .getByText(/^Questions —/)
        .or(page.getByText("No questions to display"))
        .first(),
    ).toBeVisible({ timeout: 10000 });
  }

  expect.soft(failures, failures.join("\n")).toEqual([]);
});
