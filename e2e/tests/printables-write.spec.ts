import { expect, test } from "@playwright/test";

import { mutationsEnabled } from "./mutation-helpers";
import { recordMutationArtifact } from "./mutation-artifacts";

const API_BASE = "https://kiarolabs-membership-service.onrender.com";

test("manage printables can save an answer key for an existing paper", async ({ page, request }) => {
  test.skip(!mutationsEnabled(), "Mutation tests are disabled for scheduled safety.");

  await page.goto("/admin");
  await page.getByRole("tab", { name: "Manage Printables" }).click();
  await expect(page.getByText("Manage Printable Papers")).toBeVisible({ timeout: 15000 });

  const token = await page.evaluate(() => window.localStorage.getItem("access_token"));
  expect(token, "Missing admin access token").toBeTruthy();

  const papersResponse = await request.get(`${API_BASE}/practice/math/printable/papers`);
  expect(papersResponse.ok()).toBeTruthy();
  const papersPayload = await papersResponse.json().catch(() => []);
  const papers = Array.isArray(papersPayload) ? papersPayload : [];
  const targetPaper =
    papers.find(
      (paper: any) =>
        (paper?.questions_count ?? 0) > 0 &&
        (paper?.answers_count ?? 0) > 0 &&
        (paper?.answers_count ?? 0) === (paper?.questions_count ?? 0),
    ) ||
    null;

  test.skip(!targetPaper?.paper_code, "No printable paper with a complete answer key is available for write validation.");

  const paperCode = String(targetPaper.paper_code);

  const answersResponse = await request.get(`${API_BASE}/admin/math/printable/answers?paper_code=${encodeURIComponent(paperCode)}`, {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  expect(answersResponse.ok()).toBeTruthy();
  const answersPayload = await answersResponse.json().catch(() => ({}));
  const currentAnswers = Array.isArray(answersPayload?.answers)
    ? answersPayload.answers
        .map((answer: any) => String(answer?.correct_answer ?? "").trim())
        .filter(Boolean)
    : [];

  test.skip(currentAnswers.length === 0, `Paper ${paperCode} has no existing answers to resave.`);

  await page.getByRole("combobox").click();
  await page.getByRole("option", { name: new RegExp(paperCode, "i") }).click();

  await expect(page.getByRole("button", { name: /edit answer key/i })).toBeEnabled({ timeout: 15000 });
  await page.getByRole("button", { name: /edit answer key/i }).click();

  const inputs = page.locator('input[id^="mng-ans-"]');
  await expect(inputs.first()).toBeVisible({ timeout: 15000 });

  for (let i = 0; i < currentAnswers.length; i += 1) {
    await inputs.nth(i).fill(currentAnswers[i]);
  }

  const saveResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/admin/ingestion/maths/answer-key") &&
    response.request().method() === "POST",
  );

  await page.getByRole("button", { name: /save answer key/i }).click();

  const saveResponse = await saveResponsePromise;
  const saveRawText = await saveResponse.text();
  let savePayload: any = {};
  try {
    savePayload = saveRawText ? JSON.parse(saveRawText) : {};
  } catch {
    savePayload = { raw: saveRawText };
  }

  expect(
    saveResponse.ok(),
    JSON.stringify({
      status: saveResponse.status(),
      statusText: saveResponse.statusText(),
      body: savePayload,
    }),
  ).toBeTruthy();

  await expect(page.getByText("Answer key saved successfully").first()).toBeVisible({ timeout: 15000 });

  recordMutationArtifact("printable_answer_key_save", {
    paper_code: paperCode,
    answers_saved: currentAnswers.length,
    first_answer: currentAnswers[0],
  });
});
