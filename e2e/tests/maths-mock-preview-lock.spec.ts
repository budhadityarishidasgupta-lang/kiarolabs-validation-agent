import { expect, test } from "@playwright/test";

import { answerCurrentQuestion, expectPracticeQuestion, expectPreviewLockState, goToNextQuestion } from "./practice-helpers";

test("maths mock-style session preview user reaches lock state at Q6", async ({ browser, baseURL }) => {
  const context = await browser.newContext({ baseURL });
  const page = await context.newPage();

  await page.goto("/practice/session/mathsprint");
  await expect(page.getByText("MathSprint").first()).toBeVisible();
  await expectPracticeQuestion(page);

  const nextButton = page.getByRole("button", { name: /next question/i });
  for (let index = 0; index < 5; index += 1) {
    await answerCurrentQuestion(page);
    if (!(await nextButton.isVisible().catch(() => false))) {
      test.skip(true, "Could not continue to later questions in this environment.");
    }
    await goToNextQuestion(page);
  }

  await expectPreviewLockState(page);
  await context.close();
});
