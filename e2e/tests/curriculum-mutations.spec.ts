import { expect, test } from "@playwright/test";

import { mutationsEnabled } from "./mutation-helpers";

test("curriculum admin can create a maths lesson", async ({ page, request }) => {
  test.skip(!mutationsEnabled(), "Mutation tests are disabled for scheduled safety.");

  const uniqueSuffix = Date.now();
  const lessonName = `E2E Maths Lesson ${uniqueSuffix}`;
  const displayName = `E2E Display ${uniqueSuffix}`;

  await page.goto("/admin");
  await page.getByRole("tab", { name: "Curriculum" }).click();

  await expect(page.getByRole("tab", { name: "Maths" })).toBeVisible({ timeout: 15000 });
  await page.getByRole("tab", { name: "Maths" }).click();
  const activeMathsPanel = page.locator('[data-state="active"]').filter({
    has: page.getByText("Create Lesson"),
  }).first();
  await expect(activeMathsPanel.getByText("Create Lesson")).toBeVisible({ timeout: 15000 });

  const lessonNameField = activeMathsPanel.getByRole("textbox").first();
  const displayNameField = activeMathsPanel.getByPlaceholder("Optional friendly label");
  const topicField = activeMathsPanel.locator('input[placeholder="e.g. Fractions"]');
  const difficultyField = activeMathsPanel.locator('input[placeholder="e.g. beginner"]');

  await expect(lessonNameField).toBeVisible({ timeout: 10000 });
  await expect(displayNameField).toBeVisible({ timeout: 10000 });
  await expect(topicField).toBeVisible({ timeout: 10000 });
  await expect(difficultyField).toBeVisible({ timeout: 10000 });

  await lessonNameField.fill(lessonName);
  await displayNameField.fill(displayName);
  await topicField.fill("E2E Topic");
  await difficultyField.fill("beginner");

  await expect(lessonNameField).toHaveValue(lessonName);
  await expect(displayNameField).toHaveValue(displayName);
  await expect(topicField).toHaveValue("E2E Topic");
  await expect(difficultyField).toHaveValue("beginner");

  const token = await page.evaluate(() => window.localStorage.getItem("access_token"));
  expect(token, "Missing admin access token").toBeTruthy();

  const createResponse = await request.post(
    "https://kiarolabs-membership-service.onrender.com/admin/curriculum/maths/lessons",
    {
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        Authorization: `Bearer ${token}`,
      },
      data: {
        lesson_name: lessonName,
        display_name: displayName,
        topic: "E2E Topic",
        difficulty: "beginner",
        is_active: true,
      },
    },
  );

  const createPayload = await createResponse.json().catch(() => ({}));
  expect(createResponse.ok(), JSON.stringify(createPayload)).toBeTruthy();
  expect(createPayload?.data?.display_name).toBe(displayName);

  await page.reload({ waitUntil: "domcontentloaded" });
  await page.getByRole("tab", { name: "Curriculum" }).click();
  await page.getByRole("tab", { name: "Maths" }).click();
  await expect(page.getByText(displayName)).toBeVisible({ timeout: 15000 });
});
