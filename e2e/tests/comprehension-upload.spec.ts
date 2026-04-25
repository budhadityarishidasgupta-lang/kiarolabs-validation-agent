import { expect, test } from "@playwright/test";

import { mutationsEnabled } from "./mutation-helpers";

test("comprehension admin can upload a CSV and see the new passage", async ({ page }) => {
  test.skip(!mutationsEnabled(), "Mutation tests are disabled for scheduled safety.");

  const uniqueSuffix = Date.now();
  const title = `E2E Comprehension ${uniqueSuffix}`;
  const csv = [
    "new_passage,title,passage_text,difficulty,question_text,option_a,option_b,option_c,option_d,correct_answer,question_type,sort_order",
    `1,"${title}","A short passage for end-to-end validation.","foundation","What is this test for?","Maths","Comprehension upload","Spelling","Words","B","comprehension",1`,
  ].join("\n");

  await page.goto("/admin");
  await page.getByRole("tab", { name: "Comprehension" }).click();

  await expect(page.getByText("Upload Comprehension CSV")).toBeVisible({ timeout: 15000 });

  const uploadResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/practice/comprehension/upload") &&
    response.request().method() === "POST",
  );

  await page.locator('input[type="file"]').setInputFiles({
    name: `comprehension-${uniqueSuffix}.csv`,
    mimeType: "text/csv",
    buffer: Buffer.from(csv, "utf-8"),
  });

  await page.getByRole("button", { name: /upload passages/i }).click();

  const uploadResponse = await uploadResponsePromise;
  const uploadRawText = await uploadResponse.text();
  let uploadPayload: any = {};
  try {
    uploadPayload = uploadRawText ? JSON.parse(uploadRawText) : {};
  } catch {
    uploadPayload = { raw: uploadRawText };
  }

  expect(
    uploadResponse.ok(),
    JSON.stringify({
      status: uploadResponse.status(),
      statusText: uploadResponse.statusText(),
      body: uploadPayload,
    }),
  ).toBeTruthy();

  await expect(page.getByText("Upload successful")).toBeVisible({ timeout: 15000 });
  await expect(page.getByText(title)).toBeVisible({ timeout: 15000 });
});
