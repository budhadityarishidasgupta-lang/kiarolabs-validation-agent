import { expect, test } from "@playwright/test";

import {
  answerCurrentQuestion,
  expectPracticeQuestion,
  goToNextQuestion,
  monitorPracticeFailures,
} from "./practice-helpers";

test("spelling practice loads, submits, and advances", async ({ page }) => {
  const failures: string[] = [];
  monitorPracticeFailures(page, failures);

  await page.goto("/practice/session/spellingsprint");

  await expect(page.getByText("SpellingSprint").first()).toBeVisible();
  await expectPracticeQuestion(page);
  await answerCurrentQuestion(page, "test");
  await goToNextQuestion(page);

  expect.soft(failures, failures.join("\n")).toEqual([]);
});
