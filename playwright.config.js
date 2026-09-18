import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',

  timeout: 15_000,

  expect: {
    timeout: 5_000,
  },

  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  webServer: {
    command: 'npm run preview -- --host 127.0.0.1 --port 4173',
    url: 'http://127.0.0.1:4173',
    timeout: 60_000,
    reuseExistingServer: !process.env.CI,
  },
});