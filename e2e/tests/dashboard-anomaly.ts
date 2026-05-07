import type { Page } from "@playwright/test";

const DASHBOARD_ENDPOINT_HINTS = [
  "/dashboard/insights",
  "/practice/engagement",
  "/practice/progress/weekly-improvement",
  "/practice/resume",
  "/dashboard",
] as const;

export type DashboardRequestRecord = {
  url: string;
  method: string;
  status?: number;
  failure?: string;
  contentType?: string;
  json?: any;
};

export type DashboardMonitorState = {
  consoleErrors: string[];
  networkFailures: string[];
  requests: DashboardRequestRecord[];
};

export type DashboardUiSnapshot = {
  visibleSections: string[];
  topStatusBarSignals: string[];
  moduleCardCount: number;
  purchaseCtaCount: number;
  bodyTextLength: number;
  bodyText: string;
};

export type DashboardAnomalyReport = {
  anomaly_score: number;
  status: "pass" | "warn" | "fail";
  evidence: string[];
  screenshot_path: string;
};

function isDashboardRelevantUrl(url: string): boolean {
  return DASHBOARD_ENDPOINT_HINTS.some((hint) => url.includes(hint));
}

function extractModuleObjects(record?: DashboardRequestRecord): Record<string, any> {
  const payload = record?.json;
  if (!payload || typeof payload !== "object") return {};
  const modules = (payload as Record<string, any>).modules;
  return modules && typeof modules === "object" ? modules : {};
}

function dashboardDataSummary(records: DashboardRequestRecord[]) {
  const dashboardRecord = records.find(
    (record) =>
      record.url.includes("/dashboard") &&
      record.contentType?.includes("application/json"),
  );
  const modules = extractModuleObjects(dashboardRecord);
  const moduleValues = Object.values(modules).filter(
    (value) => value && typeof value === "object",
  ) as Record<string, any>[];

  const totalAttempts = moduleValues.reduce(
    (sum, moduleData) => sum + Number(moduleData.attempts || 0),
    0,
  );
  const allLocked =
    moduleValues.length > 0 &&
    moduleValues.every((moduleData) => moduleData.unlocked === false);
  const anyApiData =
    totalAttempts > 0 ||
    moduleValues.some(
      (moduleData) =>
        Number(moduleData.accuracy || 0) > 0 ||
        Number(moduleData.completed_lessons || 0) > 0 ||
        Number(moduleData.total_lessons || 0) > 0,
    );

  const hasBlankAccuracyValue = (value: unknown) => {
    if (value === null || value === undefined) return true;
    if (typeof value !== "string") return false;
    const trimmed = value.trim();
    return trimmed === "" || trimmed === "-";
  };

  const hasAttemptsButNoAccuracyValue = moduleValues.some(
    (moduleData) =>
      Number(moduleData.attempts || 0) > 0 &&
      hasBlankAccuracyValue(moduleData.accuracy),
  );

  const hasZeroCompletionWithLessonTotals = moduleValues.some(
    (moduleData) =>
      Number(moduleData.total_lessons || 0) > 0 &&
      Number(moduleData.completed_lessons || 0) === 0 &&
      Number(moduleData.attempts || 0) > 0,
  );

  return {
    totalAttempts,
    allLocked,
    anyApiData,
    hasAttemptsButNoAccuracyValue,
    hasZeroCompletionWithLessonTotals,
  };
}

export function createDashboardMonitor(page: Page): DashboardMonitorState {
  const state: DashboardMonitorState = {
    consoleErrors: [],
    networkFailures: [],
    requests: [],
  };

  page.on("console", (message) => {
    if (message.type() !== "error") return;
    state.consoleErrors.push(message.text());
  });

  page.on("requestfailed", (request) => {
    if (!isDashboardRelevantUrl(request.url())) return;

    const failure = request.failure()?.errorText || "unknown";
    state.networkFailures.push(
      `REQUEST_FAILED ${request.method()} ${request.url()} :: ${failure}`,
    );
    state.requests.push({
      url: request.url(),
      method: request.method(),
      failure,
    });
  });

  page.on("response", async (response) => {
    if (!isDashboardRelevantUrl(response.url())) return;

    const contentType = response.headers()["content-type"] || "";
    const record: DashboardRequestRecord = {
      url: response.url(),
      method: response.request().method(),
      status: response.status(),
      contentType,
    };

    if (response.status() >= 400) {
      state.networkFailures.push(
        `HTTP_${response.status()} ${response.request().method()} ${response.url()}`,
      );
    }

    if (contentType.includes("application/json")) {
      try {
        record.json = await response.json();
      } catch {
        record.json = undefined;
      }
    }

    state.requests.push(record);
  });

  return state;
}

export async function collectDashboardUiSnapshot(page: Page): Promise<DashboardUiSnapshot> {
  const visibleSections: string[] = [];
  for (const section of [
    "Continue practice",
    "Your stats",
    "Accuracy by module",
    "Module completion",
  ]) {
    const visible = await page.getByText(section).first().isVisible().catch(() => false);
    if (visible) visibleSections.push(section);
  }

  const topStatusBarSignals: string[] = [];
  const signalMatchers: Array<[string, RegExp]> = [
    ["XP", /\bXP\b/i],
    ["day_or_days", /\bday\b|\bdays\b/i],
    ["accuracy", /accuracy/i],
    ["Week", /\bWeek\b/i],
  ];
  for (const [label, pattern] of signalMatchers) {
    const visible = await page.getByText(pattern).first().isVisible().catch(() => false);
    if (visible) topStatusBarSignals.push(label);
  }

  const moduleCardLocator = page.locator("section,article,div").filter({
    has: page.getByText(/spelling|words|math|maths|comprehension/i),
  });
  const moduleCardCount = await moduleCardLocator.count().catch(() => 0);

  const purchaseCtaLocator = page.getByRole("link").filter({
    hasText: /purchase|unlock|subscribe|buy/i,
  });
  const purchaseButtonLocator = page.getByRole("button").filter({
    hasText: /purchase|unlock|subscribe|buy/i,
  });
  const purchaseCtaCount =
    (await purchaseCtaLocator.count().catch(() => 0)) +
    (await purchaseButtonLocator.count().catch(() => 0));

  const bodyText = await page.locator("body").innerText().catch(() => "");

  return {
    visibleSections,
    topStatusBarSignals,
    moduleCardCount,
    purchaseCtaCount,
    bodyTextLength: bodyText.trim().length,
    bodyText,
  };
}

export function classifyDashboardAnomaly(input: {
  ui: DashboardUiSnapshot;
  monitor: DashboardMonitorState;
  screenshotPath: string;
  credentialKind: "admin" | "student";
}): DashboardAnomalyReport {
  const evidence: string[] = [];
  let anomalyScore = 0;
  let status: "pass" | "warn" | "fail" = "pass";

  const { ui, monitor, screenshotPath, credentialKind } = input;
  const apiSummary = dashboardDataSummary(monitor.requests);

  if (monitor.consoleErrors.length > 0) {
    anomalyScore = Math.max(anomalyScore, 100);
    status = "fail";
    evidence.push(`Console crash/errors observed: ${monitor.consoleErrors.join(" | ")}`);
  }

  if (monitor.networkFailures.length > 0) {
    anomalyScore = Math.max(anomalyScore, 100);
    status = "fail";
    evidence.push(
      `Dashboard endpoint network failure observed: ${monitor.networkFailures.join(" | ")}`,
    );
  }

  const blankDashboardShell =
    ui.visibleSections.length === 0 &&
    ui.moduleCardCount === 0 &&
    ui.topStatusBarSignals.length === 0 &&
    ui.bodyTextLength < 120;
  if (blankDashboardShell) {
    anomalyScore = Math.max(anomalyScore, 100);
    status = "fail";
    evidence.push(
      "Dashboard appears blank: no visible sections, module cards, or status bar signals.",
    );
  }

  if (ui.moduleCardCount === 0) {
    anomalyScore = Math.max(anomalyScore, 95);
    status = "fail";
    evidence.push("All module cards are missing.");
  }

  if (credentialKind === "admin" && apiSummary.allLocked) {
    anomalyScore = Math.max(anomalyScore, 95);
    status = "fail";
    evidence.push("Admin credentials appear to see all modules locked.");
  }

  if (apiSummary.anyApiData && ui.moduleCardCount === 0) {
    anomalyScore = Math.max(anomalyScore, 100);
    status = "fail";
    evidence.push("Dashboard API shows module/progress data but the UI shows blank cards.");
  }

  if (status !== "fail" && apiSummary.hasAttemptsButNoAccuracyValue) {
    anomalyScore = Math.max(anomalyScore, 45);
    status = "warn";
    evidence.push("API shows attempts, but at least one module has no usable accuracy value.");
  }

  if (status !== "fail" && apiSummary.hasZeroCompletionWithLessonTotals) {
    anomalyScore = Math.max(anomalyScore, 35);
    status = "warn";
    evidence.push(
      "Module completion is zero despite lesson totals and prior attempts existing in API data.",
    );
  }

  const looksLikeValidNewUser =
    apiSummary.totalAttempts === 0 &&
    !apiSummary.anyApiData &&
    ui.moduleCardCount > 0;
  if (looksLikeValidNewUser) {
    evidence.push(
      "Valid empty/new-user dashboard state detected: zero attempts with visible module cards.",
    );
  }

  if (ui.purchaseCtaCount > 0 && apiSummary.allLocked) {
    evidence.push("Locked-module purchase CTA state detected.");
  }

  if (status === "pass" && ui.visibleSections.length < 4 && ui.moduleCardCount > 0) {
    anomalyScore = Math.max(anomalyScore, 25);
    status = "warn";
    evidence.push("Dashboard shell is present, but one or more expected sections are missing.");
  }

  if (status === "pass" && ui.topStatusBarSignals.length < 4) {
    anomalyScore = Math.max(anomalyScore, 20);
    status = "warn";
    evidence.push("Top status bar is partially rendered or missing one of the expected signals.");
  }

  if (status === "pass" && evidence.length === 0) {
    evidence.push(
      "Dashboard rendered expected shell, cards, and no crash/network regression was observed.",
    );
  }

  return {
    anomaly_score: anomalyScore,
    status,
    evidence,
    screenshot_path: screenshotPath,
  };
}
