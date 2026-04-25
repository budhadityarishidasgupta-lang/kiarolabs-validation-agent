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
  const addLessonButton = activeMathsPanel.getByRole("button", { name: /add lesson/i });
  await expect(addLessonButton).toBeEnabled();

  const createResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/admin/curriculum/maths/lessons") &&
    response.request().method() === "POST",
  );

  const refreshResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/admin/curriculum/maths/lessons") &&
    response.request().method() === "GET",
  );

  await addLessonButton.click();

  const createResponse = await createResponsePromise;
  expect(createResponse.ok()).toBeTruthy();

  const createPayload = await createResponse.json();
  expect(createPayload?.data?.display_name).toBe(displayName);

  const refreshResponse = await refreshResponsePromise;
  expect(refreshResponse.ok()).toBeTruthy();

  const refreshPayload = await refreshResponse.json();
  const lessons = Array.isArray(refreshPayload?.data) ? refreshPayload.data : [];
  expect(lessons.some((lesson: any) => lesson?.display_name === displayName)).toBeTruthy();

  await expect(page.getByText("Lesson created")).toBeVisible({ timeout: 10000 });
});
