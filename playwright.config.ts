import { defineConfig } from "@playwright/test";

export const backendUrl = "http://127.0.0.1:8001";
export const databaseFile = "e2e/undercover-e2e.db";

export default defineConfig({
  testDir: "e2e",
  outputDir: "e2e/test-results",
  reporter: "list",
  globalSetup: "./e2e/global-setup.ts",
  use: { baseURL: "http://localhost:5174" },
  webServer: [
    {
      command: "uv run -m uvicorn backend.main:app --port 8001",
      url: `${backendUrl}/api/health`,
      env: { UNDERCOVER_DB: databaseFile },
      reuseExistingServer: false,
    },
    {
      command: "npx vite dashboard --port 5174 --strictPort",
      url: "http://localhost:5174",
      env: { UNDERCOVER_BACKEND: backendUrl },
      reuseExistingServer: false,
    },
  ],
});
