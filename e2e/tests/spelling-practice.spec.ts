import { expect, test } from "@playwright/test";

import {
  expectPracticeQuestion,
  monitorPracticeFailures,
} from "./practice-helpers";

test("spelling practice loads, submits, and advances", async ({ page }) => {
  const failures: string[] = [];
  let latestQuestionPayload: any = null;
  let latestSubmitPayload: any = null;
  monitorPracticeFailures(page, failures);

  page.on("response", async (response) => {
    if (!response.url().includes("/practice/spelling/question") || response.request().method() !== "GET") {
      if (!response.url().includes("/practice/spelling/answer") || response.request().method() !== "POST") {
        return;
      }

      try {
        latestSubmitPayload = await response.json();
      } catch {
        latestSubmitPayload = null;
      }
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
  await expect(page.getByRole("button", { name: /submit answer/i })).toBeVisible();

  expect.soft((latestQuestionPayload?.example_sentence ?? null), "Pre-submit spelling question leaked example_sentence").toBeNull();

  const encouragementMessage = (latestQuestionPayload?.encouragement_message ?? "").trim();
  const reviewBanner = encouragementMessage
    ? page.getByText(encouragementMessage).first()
    : page.getByText(/you were close last time|review question|revisit this/i).first();

  const reviewVisible = Boolean(
    latestQuestionPayload?.is_review || latestQuestionPayload?.session_state?.is_review,
  );

  await expect(page.getByText(/He made a complaint|The aggressive dog|".*"/).first()).toHaveCount(0);

  if (reviewVisible) {
    await expect(reviewBanner).toBeVisible();
    await expect(page.getByText(encouragementMessage).first()).toBeVisible();
  } else {
    if (encouragementMessage) {
      throw new Error(
        `Ordinary spelling question leaked encouragement_message: ${JSON.stringify(latestQuestionPayload)}`,
      );
    }
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
  if (latestSubmitPayload?.correct_word) {
    await expect(page.getByText(String(latestSubmitPayload.correct_word)).first()).toBeVisible();
  }

  expect.soft(failures, failures.join("\n")).toEqual([]);
});
