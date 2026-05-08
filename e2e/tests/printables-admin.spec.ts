import { expect, test } from "@playwright/test";

const API_BASE = "https://kiarolabs-membership-service.onrender.com";

test("manage printables tab loads and inspects a paper", async ({ page, request }) => {
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

  await expect(page.getByText("Manage Printable Papers")).toBeVisible({ timeout: 15000 });

  const papersResponse = await request.get(`${API_BASE}/practice/math/printable/papers`);
  expect(papersResponse.ok()).toBeTruthy();
  const papersPayload = await papersResponse.json().catch(() => []);
  const papers = Array.isArray(papersPayload) ? papersPayload : [];
  const targetPaper =
    papers.find((paper: any) => String(paper?.paper_code ?? paper?.code ?? "").trim().length > 0) ?? null;

  test.skip(!targetPaper, "No printable papers are available for read-only validation.");

  const paperCode = String(targetPaper?.paper_code ?? targetPaper?.code ?? "");
  const paperCombobox = page
    .getByRole("combobox")
    .filter({ hasText: /Choose a paper|Loading papers/i })
    .first();

  await expect(paperCombobox).toBeVisible({ timeout: 10000 });
  await expect(paperCombobox).toBeEnabled({ timeout: 10000 });
  await paperCombobox.click();

  const noPapersOption = page.getByText("No papers found");
  if (await noPapersOption.isVisible().catch(() => false)) {
    test.skip(true, "No printable papers are visible in the paper selector.");
  }

  const paperOption = page.getByRole("option", { name: new RegExp(paperCode, "i") }).first();
  await expect(paperOption).toBeVisible({ timeout: 10000 });
  await paperOption.click();

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
        .getByText(/^Questions/)
        .or(page.getByText("No questions to display"))
        .first(),
    ).toBeVisible({ timeout: 10000 });
  }

  expect.soft(failures, failures.join("\n")).toEqual([]);
});
