import { expect, test } from "@playwright/test";

import {
  expectPracticeQuestion,
  monitorPracticeFailures,
} from "./practice-helpers";

test("spelling practice loads, submits, and advances", async ({ page }) => {
  const failures: string[] = [];
  let latestQuestionPayload: any = null;
  monitorPracticeFailures(page, failures);

  page.on("response", async (response) => {
    if (!response.url().includes("/practice/spelling/question") || response.request().method() !== "GET") {
      return;
    }

    try {
      latestQuestionPayload = await response.json();
    } catch {
      latestQuestionPayload = null;
    }
  });

  await page.goto("/practice/session/spellingsprint");

  await expect(page.getByText("SpellingSprint").first()).toBeVisible();
  await expectPracticeQuestion(page);

  const reviewBanner = page.getByText("Review Return").first();
  if ((latestQuestionPayload?.encouragement_message ?? "").trim()) {
    await expect(reviewBanner).toBeVisible();
    await expect(page.getByText(latestQuestionPayload.encouragement_message).first()).toBeVisible();
  } else {
    await expect(reviewBanner).toHaveCount(0);
  }

  const textInput = page.locator('input[type="text"]').first();
  await textInput.fill("__validation_wrong__");
  await page.getByRole("button", { name: /submit answer/i }).click();

  const feedbackStatus = page
    .locator('[aria-live="polite"], [role="status"]')
    .filter({ hasText: /Not quite right|Correct/i })
    .first();

  await expect(feedbackStatus).toBeVisible({ timeout: 10000 });
  await expect(page.getByText("Not quite right").first()).toBeVisible();
  await expect(page.getByText("Correct answer").first()).toBeVisible();

  expect.soft(failures, failures.join("\n")).toEqual([]);
});
