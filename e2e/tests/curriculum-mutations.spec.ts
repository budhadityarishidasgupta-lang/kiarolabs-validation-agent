import { expect, test } from "@playwright/test";

import { recordMutationArtifact } from "./mutation-artifacts";
import { mutationsEnabled } from "./mutation-helpers";

const MEMBERSHIP_API = "https://kiarolabs-membership-service.onrender.com";

async function cleanupE2EMathsLessons(request: any, token: string) {
  const lessonsResponse = await request.get(`${MEMBERSHIP_API}/admin/curriculum/maths/lessons`, {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
  expect(lessonsResponse.ok(), `Failed to list maths lessons: ${lessonsResponse.status()}`).toBeTruthy();
  const payload = await lessonsResponse.json().catch(() => ({}));
  const lessons = Array.isArray(payload?.data) ? payload.data : [];
  const leaked = lessons.filter((lesson: any) => {
    const lessonName = String(lesson?.lesson_name ?? "");
    const displayName = String(lesson?.display_name ?? "");
    const topic = String(lesson?.topic ?? "");
    return /^e2e/i.test(lessonName) || /^e2e/i.test(displayName) || /^e2e/i.test(topic);
  });

  for (const lesson of leaked) {
    const deleteResponse = await request.delete(
      `${MEMBERSHIP_API}/admin/curriculum/maths/lessons/${lesson.lesson_id}`,
      {
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
        },
      },
    );
    expect(
      deleteResponse.ok(),
      `Failed to delete leaked maths lesson ${lesson.lesson_id}: ${deleteResponse.status()}`,
    ).toBeTruthy();
  }
}

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

  await cleanupE2EMathsLessons(request, token);

  let createdLessonId: number | null = null;

  try {
    const createResponse = await request.post(
      `${MEMBERSHIP_API}/admin/curriculum/maths/lessons`,
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

    const createRawText = await createResponse.text();
    let createPayload: any = {};
    try {
      createPayload = createRawText ? JSON.parse(createRawText) : {};
    } catch {
      createPayload = { raw: createRawText };
    }

    expect(
      createResponse.ok(),
      JSON.stringify({
        status: createResponse.status(),
        statusText: createResponse.statusText(),
        body: createPayload,
      }),
    ).toBeTruthy();
    expect(createPayload?.data?.display_name).toBe(displayName);
    createdLessonId = Number(createPayload?.data?.lesson_id || 0) || null;

    await page.reload({ waitUntil: "domcontentloaded" });
    await page.getByRole("tab", { name: "Curriculum" }).click();
    await page.getByRole("tab", { name: "Maths" }).click();
    await expect(page.getByText(displayName)).toBeVisible({ timeout: 15000 });

    recordMutationArtifact("maths_lesson_create", {
      display_name: displayName,
      lesson_name: lessonName,
      lesson_code: createPayload?.data?.lesson_code,
      cleaned_up: true,
    });
  } finally {
    if (createdLessonId) {
      const deleteResponse = await request.delete(
        `${MEMBERSHIP_API}/admin/curriculum/maths/lessons/${createdLessonId}`,
        {
          headers: {
            Accept: "application/json",
            Authorization: `Bearer ${token}`,
          },
        },
      );
      expect(
        deleteResponse.ok(),
        `Failed to delete created maths lesson ${createdLessonId}: ${deleteResponse.status()}`,
      ).toBeTruthy();
    }
  }
});
