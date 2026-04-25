import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL || "https://kiarolabs.com";

export default defineConfig({
  testDir: "./e2e/tests",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["json", { outputFile: "reports/e2e-latest.json" }]
  ],
  use: {
    baseURL,
    trace: "on-first-retry",
    video: "retain-on-failure",
    screenshot: "only-on-failure"
  },
  projects: [
    {
      name: "setup",
      testMatch: /.*\.setup\.ts/
    },
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: ".auth/admin.json"
      },
      dependencies: ["setup"]
    }
  ]
});
