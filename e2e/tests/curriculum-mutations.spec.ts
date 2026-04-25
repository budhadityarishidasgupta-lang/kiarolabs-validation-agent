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
  await expect(page.getByText("Create Lesson")).toBeVisible({ timeout: 15000 });

  const textboxes = page.locator("input:visible");

  await textboxes.nth(0).fill(lessonName);
  await textboxes.nth(1).fill(displayName);
  await textboxes.nth(2).fill("E2E Topic");
  await textboxes.nth(3).fill("beginner");

  const createResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/admin/curriculum/maths/lessons") &&
    response.request().method() === "POST",
  );

  const refreshResponsePromise = page.waitForResponse((response) =>
    response.url().includes("/admin/curriculum/maths/lessons") &&
    response.request().method() === "GET",
  );

  await page.getByRole("button", { name: /add lesson/i }).click();

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
