import { expect, test } from "@playwright/test";

import {
  answerCurrentQuestion,
  expectPracticeQuestion,
  goToNextQuestion,
  monitorPracticeFailures,
} from "./practice-helpers";

test("words practice loads, submits, and advances", async ({ page }) => {
  const failures: string[] = [];
  monitorPracticeFailures(page, failures);

  await page.goto("/practice/session/wordsprint");

  await expect(page.getByText("WordSprint").first()).toBeVisible();
  await expectPracticeQuestion(page);
  await answerCurrentQuestion(page);
  await goToNextQuestion(page);

  expect.soft(failures, failures.join("\n")).toEqual([]);
});
