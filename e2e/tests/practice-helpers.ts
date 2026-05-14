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
  const submitButton = page
    .getByTestId("submit-answer")
    .or(page.getByRole("button", { name: /submit answer/i }))
    .first();
  const questionLabel = page
    .getByTestId("question-counter")
    .or(page.getByText(/^Question\s+\d+/i).first())
    .first();
  const emptyState = page.getByText(
    /No question available|No questions available|No question available for this lesson yet|Select a lesson to begin practice|Choose a lesson from the side panel/i,
  );

  await expect(submitButton.or(emptyState).first()).toBeVisible({ timeout: 20000 });

  if (await submitButton.isVisible().catch(() => false)) {
    await expect(questionLabel).toBeVisible({ timeout: 10000 });
    return;
  }

  // Some sessions briefly render an empty state before the curriculum rail auto-selects
  // the first lesson and the question payload arrives.
  await expect(submitButton.or(questionLabel).first()).toBeVisible({
    timeout: 20000,
  });

  if (await submitButton.isVisible().catch(() => false)) {
    await expect(questionLabel).toBeVisible({ timeout: 10000 });
    return;
  }

  throw new Error("Practice session reached an empty state instead of loading a question.");
}

export async function answerCurrentQuestion(page: Page, answer?: string) {
  const textInput = page.locator('input[type="text"]').first();
  const textbox = page.getByRole("textbox").first();
  const answerRegion = page.getByTestId("practice-question").or(page.locator("main")).first();
  const singleChoiceButton = answerRegion.locator("button[aria-pressed]").first();
  const multiChoiceCheckbox = answerRegion.getByRole("checkbox").first();
  const feedbackStatus = page
    .locator('[aria-live="polite"], [role="status"]')
    .filter({ hasText: /Not quite right|Correct/i })
    .first();

  if (await textInput.isVisible().catch(() => false)) {
    await textInput.fill(answer ?? "test");
  } else if (await textbox.isVisible().catch(() => false)) {
    await textbox.fill(answer ?? "test");
  } else if (await multiChoiceCheckbox.isVisible().catch(() => false)) {
    await multiChoiceCheckbox.click();
  } else if (await singleChoiceButton.isVisible().catch(() => false)) {
    await singleChoiceButton.click();
  } else {
    throw new Error("No supported answer input control found (textbox, checkbox, or option button).");
  }

  await page
    .getByTestId("submit-answer")
    .or(page.getByRole("button", { name: /submit answer/i }))
    .first()
    .click();
  await expect(feedbackStatus).toBeVisible({ timeout: 10000 });
}

export async function goToNextQuestion(page: Page) {
  const questionLabel = page
    .getByTestId("question-counter")
    .or(page.getByText(/^Question\s+\d+/i).first())
    .first();
  const currentQuestionLabel = (await questionLabel.textContent().catch(() => null))?.trim() ?? null;

  await page.getByRole("button", { name: /next question/i }).click();

  if (currentQuestionLabel) {
    await expect(questionLabel).not.toHaveText(currentQuestionLabel, { timeout: 10000 });
    return;
  }

  await expect(questionLabel).toBeVisible({ timeout: 10000 });
}

export async function expectPreviewLockState(page: Page) {
  const lockIndicator = page.getByText(
    /locked|unlock full access|preview limit|question 6|continue practice|complete mock exam/i,
  );
  await expect(lockIndicator.first()).toBeVisible({ timeout: 15000 });
}
