import { expect, test, type Page, type TestInfo } from "@playwright/test";
import {
  classifyDashboardAnomaly,
  collectDashboardUiSnapshot,
  createDashboardMonitor,
} from "./dashboard-anomaly";

function credentialsFromEnv() {
  const email = process.env.E2E_ADMIN_EMAIL || process.env.E2E_STUDENT_EMAIL;
  const password = process.env.E2E_ADMIN_PASSWORD || process.env.E2E_STUDENT_PASSWORD;

  if (!email || !password) {
    throw new Error(
      "Set E2E_ADMIN_EMAIL/E2E_ADMIN_PASSWORD or E2E_STUDENT_EMAIL/E2E_STUDENT_PASSWORD",
    );
  }

  return { email, password };
}

function credentialKindFromEnv(): "admin" | "student" {
  return process.env.E2E_ADMIN_EMAIL ? "admin" : "student";
}

async function ensureDashboardSession(page: Page) {
  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });

  if (/\/login(?:[/?#]|$)/.test(page.url())) {
    const { email, password } = credentialsFromEnv();

    await expect(page.getByRole("heading", { name: "Sign In to Your Account" })).toBeVisible({
      timeout: 30000,
    });
    await page.getByPlaceholder("you@example.com").fill(email);
    await page.locator('input[type="password"]').first().fill(password);
    await page.getByRole("button", { name: "Sign In" }).click();
    await page.waitForURL(/\/dashboard(?:[/?#]|$)/, { timeout: 30000 });
  }

  await expect(page).toHaveURL(/\/dashboard(?:[/?#]|$)/);
}

async function attachFailureTelemetry(
  testInfo: TestInfo,
  consoleErrors: string[],
  networkFailures: string[],
  anomalyReportText?: string,
) {
  if (consoleErrors.length > 0) {
    await testInfo.attach("dashboard-console-errors", {
      body: consoleErrors.join("\n"),
      contentType: "text/plain",
    });
  }

  if (networkFailures.length > 0) {
    await testInfo.attach("dashboard-network-failures", {
      body: networkFailures.join("\n"),
      contentType: "text/plain",
    });
  }

  if (anomalyReportText) {
    await testInfo.attach("dashboard-anomaly-report", {
      body: anomalyReportText,
      contentType: "application/json",
    });
  }
}

test("dashboard deployment smoke", async ({ page }, testInfo) => {
  const credentialKind = credentialKindFromEnv();
  const monitor = createDashboardMonitor(page);
  const screenshotPath = testInfo.outputPath("dashboard-anomaly.png");
  let anomalyReportText = "";

  try {
    await ensureDashboardSession(page);
    await page.waitForLoadState("domcontentloaded");
    await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => {});

    const uiSnapshot = await collectDashboardUiSnapshot(page);
    const anomalyReport = classifyDashboardAnomaly({
      ui: uiSnapshot,
      monitor,
      screenshotPath,
      credentialKind,
    });
    anomalyReportText = JSON.stringify(anomalyReport, null, 2);

    expect.soft(
      anomalyReport.status,
      `Dashboard anomaly score=${anomalyReport.anomaly_score}\n${anomalyReport.evidence.join("\n")}`,
    ).not.toBe("fail");
  } catch (error) {
    anomalyReportText = JSON.stringify(
      {
        anomaly_score: 100,
        status: "fail",
        evidence: [
          `Dashboard smoke test threw before classification: ${
            error instanceof Error ? error.message : String(error)
          }`,
          ...monitor.consoleErrors,
          ...monitor.networkFailures,
        ],
        screenshot_path: screenshotPath,
      },
      null,
      2,
    );
    throw error;
  } finally {
    await page.screenshot({ path: screenshotPath, fullPage: true }).catch(() => {});
    await attachFailureTelemetry(
      testInfo,
      monitor.consoleErrors,
      monitor.networkFailures,
      anomalyReportText,
    );
  }
});
