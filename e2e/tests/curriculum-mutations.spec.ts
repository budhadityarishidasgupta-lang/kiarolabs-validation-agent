import { expect, test } from "@playwright/test";

import { mutationsEnabled } from "./mutation-helpers";

test("curriculum admin can create a maths lesson", async ({ page }) => {
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

  const createResult = await page.evaluate(
    async ({ lessonName, displayName }) => {
      const token = window.localStorage.getItem("access_token");
      if (!token) {
        return { ok: false, error: "Missing access token" };
      }

      const response = await fetch("https://kiarolabs-membership-service.onrender.com/admin/curriculum/maths/lessons", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          lesson_name: lessonName,
          display_name: displayName,
          topic: "E2E Topic",
          difficulty: "beginner",
          is_active: true,
        }),
      });

      const rawText = await response.text();
      let payload: any = null;
      try {
        payload = rawText ? JSON.parse(rawText) : null;
      } catch {
        payload = rawText;
      }

      return {
        ok: response.ok,
        status: response.status,
        payload,
      };
    },
    { lessonName, displayName },
  );

  expect(createResult.ok, JSON.stringify(createResult)).toBeTruthy();
  expect(createResult.payload?.data?.display_name).toBe(displayName);

  await page.reload({ waitUntil: "domcontentloaded" });
  await page.getByRole("tab", { name: "Curriculum" }).click();
  await page.getByRole("tab", { name: "Maths" }).click();
  await expect(page.getByText(displayName)).toBeVisible({ timeout: 15000 });
});
