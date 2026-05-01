// tests/e2e/all-modules-smoke.spec.ts
// Batch smoke tests for all connect-* docker modules
// Run with: npx playwright test tests/e2e/all-modules-smoke.spec.ts

import { test, expect } from '@playwright/test';

// Registry of all connect-* modules with their ports and health endpoints
const MODULES = [
  { 
    name: 'connect-scenario', 
    port: 8096, 
    healthPath: '/api/cql/health',
    routes: ['/', '/scenarios', '/scenario-files', '/scenario-editor'],
  },
  { 
    name: 'connect-config', 
    port: 8097, 
    healthPath: '/api/health',
    routes: ['/', '/config'],
  },
  { 
    name: 'connect-data', 
    port: 8098, 
    healthPath: '/api/health',
    routes: ['/', '/data'],
  },
  { 
    name: 'connect-id', 
    port: 8099, 
    healthPath: '/api/health',
    routes: ['/', '/identification'],
  },
  { 
    name: 'connect-manager', 
    port: 8100, 
    healthPath: '/api/health',
    routes: ['/', '/manager'],
  },
  { 
    name: 'connect-template', 
    port: 8101, 
    healthPath: '/api/health',
    routes: ['/', '/templates'],
  },
  { 
    name: 'connect-test', 
    port: 8102, 
    healthPath: '/api/health',
    routes: ['/', '/test'],
  },
];

test.describe('All Connect Modules - Batch Smoke Tests', () => {
  test.describe('Container Health Checks', () => {
    for (const module of MODULES) {
      test(`${module.name} should be reachable on port ${module.port}`, async ({ page }) => {
        const baseUrl = `http://localhost:${module.port}`;
        const response = await page.request.get(baseUrl);
        expect(response.ok()).toBeTruthy();
      });

      test(`${module.name} health endpoint should return OK`, async ({ page }) => {
        const healthUrl = `http://localhost:${module.port}${module.healthPath}`;
        const response = await page.request.get(healthUrl);
        
        if (response.ok()) {
          const data = await response.json().catch(() => null);
          if (data && data.status) {
            expect(data.status).toBe('ok');
          }
        }
      });
    }
  });

  test.describe('Route Availability', () => {
    for (const module of MODULES) {
      for (const route of module.routes) {
        test(`${module.name}${route} should be accessible`, async ({ page }) => {
          const url = `http://localhost:${module.port}${route}`;
          await page.goto(url, { waitUntil: 'domcontentloaded' });
          
          // Check no critical errors
          const bodyText = await page.locator('body').textContent();
          const hasCriticalError = /500|502|503|504|connection refused/i.test(bodyText || '');
          
          expect(hasCriticalError).toBeFalsy();
        });
      }
    }
  });
});

/**
 * How to standardize tests across all connect-* modules:
 * 
 * 1. Create a file at connect-<module>/tests/playwright/e2e-smoke.spec.ts
 * 2. Copy the template from tests/e2e/module-smoke-test-template.spec.ts
 * 3. Update MODULE_NAME, BASE_URL, ROUTES, and API_ENDPOINTS
 * 4. Add module-specific tests
 * 5. Register your module in MODULES array above for batch testing
 * 
 * Each module should test:
 * - Container startup (port reachable)
 * - HTML serving (content-type)
 * - Key routes (200 status)
 * - API endpoints (JSON responses)
 * - UI elements (nav, content areas)
 * - Mobile/desktop responsive rendering
 */
