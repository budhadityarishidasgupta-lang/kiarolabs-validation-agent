import { expect, type Page } from "@playwright/test";

export function monitorPracticeFailures(page: Page, failures: string[]) {
  page.on("response", async (response) => {
    const status = response.status();
    const url = response.url();

    if (!url.includes("/practice/")) return;

    if (status >= 500) {
      failures.push(`${status} ${url}`);
      return;
    }

    if (status === 404) {
      failures.push(`${status} ${url}`);
    }
  });
}

export async function expectPracticeQuestion(page: Page) {
  const submitButton = page.getByRole("button", { name: /submit answer/i });
  const emptyState = page.getByText(
    /No question available|No questions available|No question available for this lesson yet|Select a lesson to begin practice|Choose a lesson from the side panel/i,
  );

  await expect(submitButton.or(emptyState).first()).toBeVisible({ timeout: 20000 });

  if (await emptyState.first().isVisible()) {
    throw new Error("Practice session reached an empty state instead of loading a question.");
  }

  await expect(page.getByText(/^Question 1/)).toBeVisible({ timeout: 10000 });
}

export async function answerCurrentQuestion(page: Page, answer?: string) {
  const textInput = page.locator('input[type="text"]').first();

  if (await textInput.isVisible().catch(() => false)) {
    await textInput.fill(answer ?? "test");
  } else {
    await page.locator('button[aria-pressed]').first().click();
  }

  await page.getByRole("button", { name: /submit answer/i }).click();
  await expect(page.getByRole("status")).toBeVisible({ timeout: 10000 });
}

export async function goToNextQuestion(page: Page) {
  await page.getByRole("button", { name: /next question/i }).click();
  await expect(page.getByText(/^Question 2/)).toBeVisible({ timeout: 10000 });
}
