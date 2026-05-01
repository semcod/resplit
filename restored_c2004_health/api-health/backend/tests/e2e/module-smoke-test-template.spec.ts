// tests/e2e/module-smoke-test-template.spec.ts
// Template for standardized smoke tests across all connect-* docker modules
// 
// USAGE:
// 1. Copy this file to connect-<module>/tests/playwright/e2e-smoke.spec.ts
// 2. Update MODULE_NAME, BASE_URL, and ROUTES for your module
// 3. Add module-specific API tests
// 4. Run with: npx playwright test connect-<module>/tests/playwright/e2e-smoke.spec.ts

import { test, expect, Page } from '@playwright/test';

// ============================================================================
// CONFIGURATION - Update these for each module
// ============================================================================
const MODULE_NAME = 'connect-scenario';  // Change to your module name
const BASE_URL = process.env.CONNECT_SCENARIO_URL || 'http://localhost:8096';
const API_PREFIX = '/api/cql';  // Change to your API prefix

const ROUTES = [
  { path: '/', name: 'Home', required: true },
  { path: '/scenarios', name: 'Scenarios', required: true },
  { path: '/scenario-files', name: 'Scenario Files', required: true },
  { path: '/scenario-editor', name: 'Editor', required: false },
  { path: '/library-editor', name: 'Library', required: false },
  { path: '/map-editor', name: 'Map', required: false },
  { path: '/dsl-editor', name: 'DSL', required: false },
  { path: '/func-editor', name: 'Func', required: false },
];

const API_ENDPOINTS = [
  { path: '/health', method: 'GET', name: 'Health Check' },
  { path: '/capabilities', method: 'GET', name: 'Capabilities' },
  { path: '/scenario-files', method: 'GET', name: 'Scenario Files List' },
];
// ============================================================================

// Standard helpers (can be imported from shared location)
async function waitForAppReady(page: Page, timeout = 30_000): Promise<void> {
  await page.waitForFunction(() => {
    const nav = document.querySelector('.nav, nav, header');
    const main = document.querySelector('main, .main, .dashboard, #root > div');
    return !!nav || !!main;
  }, { timeout });
}

async function gotoAndWaitReady(page: Page, path: string): Promise<void> {
  await page.goto(`${BASE_URL}${path}`, { waitUntil: 'domcontentloaded' });
  await waitForAppReady(page);
}

// Standard test suite
test.describe(`${MODULE_NAME} - Standardized Smoke Tests`, () => {
  test.beforeEach(async ({ page }) => {
    page.setDefaultTimeout(30_000);
  });

  test.describe('Module Startup', () => {
    test('container should be reachable', async ({ page }) => {
      const response = await page.request.get(BASE_URL);
      expect(response.ok()).toBeTruthy();
    });

    test('should serve HTML for root path', async ({ page }) => {
      const response = await page.request.get(BASE_URL);
      const contentType = response.headers()['content-type'];
      expect(contentType).toContain('text/html');
    });
  });

  test.describe('Route Availability', () => {
    for (const route of ROUTES) {
      test(`${route.name} (${route.path}) should be accessible`, async ({ page }) => {
        await gotoAndWaitReady(page, route.path);
        
        // Check for error indicators
        const bodyText = await page.locator('body').textContent();
        const hasError = /error|błąd|not found|404|cannot/i.test(bodyText || '');
        
        if (route.required) {
          expect(hasError).toBeFalsy();
        }
      });
    }
  });

  test.describe('API Health', () => {
    for (const endpoint of API_ENDPOINTS) {
      test(`${endpoint.name} (${endpoint.path}) should respond`, async ({ page }) => {
        const url = `${BASE_URL}${API_PREFIX}${endpoint.path}`;
        const response = await page.request.get(url);
        
        // API should return 2xx status
        expect(response.status()).toBeLessThan(500);
        expect(response.status()).not.toBe(404);
      });
    }
  });

  test.describe('Common UI Elements', () => {
    test('should have navigation or header', async ({ page }) => {
      await gotoAndWaitReady(page, '/');
      
      const header = page.locator('nav, header, .nav, .header, .navbar').first();
      await expect(header).toBeVisible();
    });

    test('should have main content area', async ({ page }) => {
      await gotoAndWaitReady(page, '/');
      
      const main = page.locator('main, .main, .dashboard, .content, #root > div').first();
      await expect(main).toBeVisible();
    });
  });

  test.describe('Responsive Design', () => {
    test('should render on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await gotoAndWaitReady(page, '/');
      
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('should render on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1280, height: 720 });
      await gotoAndWaitReady(page, '/');
      
      const body = page.locator('body');
      await expect(body).toBeVisible();
    });
  });
});

/**
 * Registry of all connect-* modules for batch testing
 * Add your module here when creating smoke tests
 */
export const MODULE_REGISTRY = [
  { name: 'connect-scenario', port: 8096, healthPath: '/api/cql/health' },
  { name: 'connect-config', port: 8097, healthPath: '/api/health' },
  { name: 'connect-data', port: 8098, healthPath: '/api/health' },
  { name: 'connect-id', port: 8099, healthPath: '/api/health' },
  { name: 'connect-manager', port: 8100, healthPath: '/api/health' },
  { name: 'connect-template', port: 8101, healthPath: '/api/health' },
  { name: 'connect-test', port: 8102, healthPath: '/api/health' },
];
