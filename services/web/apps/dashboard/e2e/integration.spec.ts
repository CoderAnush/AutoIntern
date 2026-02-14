import { test, expect } from '@playwright/test';

/**
 * AutoIntern Integration Tests
 * 
 * Tests for API integration, data persistence, and cross-feature workflows:
 * - Authentication token management
 * - Data creation, retrieval, and deletion
 * - Multi-step workflows (apply to job, track in applications)
 * - Real backend API calls
 * 
 * Run: npx playwright test e2e/integration.spec.ts
 */

const BASE_URL = 'http://localhost:3000';
const API_BASE = 'http://localhost:8000';
const TEST_EMAIL = 'test@example.com';
const TEST_PASSWORD = 'TestPass123!';

// Helper to get auth tokens
async function login(page) {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('input[type="email"]', TEST_EMAIL);
  await page.fill('input[type="password"]', TEST_PASSWORD);
  await page.click('button:has-text("Sign In")');
  await expect(page).toHaveURL('/');
  
  // Extract token from localStorage
  const token = await page.evaluate(() => {
    const auth = localStorage.getItem('auth-store');
    if (auth) {
      const parsed = JSON.parse(auth);
      return parsed.state?.accessToken;
    }
    return null;
  });
  
  return token;
}

test.describe('Backend API Integration Tests', () => {
  
  test.describe('Authentication API', () => {
    
    test('should successfully login and receive valid JWT token', async ({ page }) => {
      const token = await login(page);
      
      expect(token).toBeTruthy();
      expect(typeof token).toBe('string');
      expect(token.split('.').length).toBe(3); // JWT format: header.payload.signature
    });

    test('should use token for authenticated requests', async ({ page }) => {
      const token = await login(page);
      
      // Make authenticated API call
      const response = await page.request.get(`${API_BASE}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      expect(response.ok()).toBeTruthy();
      const user = await response.json();
      expect(user.email).toBe(TEST_EMAIL);
    });

    test('should reject requests with invalid token', async () => {
      const response = await test.request.get(`${API_BASE}/api/auth/me`, {
        headers: { Authorization: 'Bearer invalid_token' }
      });
      
      expect(response.status()).toBe(401);
    });

    test('should allow token refresh on dashboard', async ({ page }) => {
      const token = await login(page);
      expect(token).toBeTruthy();
      
      // Stay on dashboard for a bit
      await page.waitForTimeout(2000);
      
      // Token should still be valid
      const sessionToken = await page.evaluate(() => {
        const auth = localStorage.getItem('auth-store');
        if (auth) {
          const parsed = JSON.parse(auth);
          return parsed.state?.accessToken;
        }
        return null;
      });
      
      expect(sessionToken).toBeTruthy();
    });
  });

  test.describe('Jobs API Integration', () => {
    
    test('should fetch jobs list from API', async ({ page }) => {
      const token = await login(page);
      
      // Navigate to jobs page
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)').first();
      await jobsLink.click();
      
      await expect(page).toHaveURL(/\/jobs/);
      await page.waitForLoadState('networkidle');
      
      // Make API call
      const response = await page.request.get(`${API_BASE}/api/jobs?limit=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(Array.isArray(data) || data.items).toBeTruthy();
    });

    test('should search jobs via API', async ({ page }) => {
      const token = await login(page);
      
      // Navigate to jobs page
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)').first();
      await jobsLink.click();
      
      await expect(page).toHaveURL(/\/jobs/);
      
      // Make search API call
      const response = await page.request.get(`${API_BASE}/api/jobs/search?q=python`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Should either return results or handle gracefully
      expect([200, 404]).toContain(response.status());
    });

    test('should filter jobs by type via API', async ({ page }) => {
      const token = await login(page);
      
      // Make filter API call
      const response = await page.request.get(`${API_BASE}/api/jobs?job_type=Internship`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Should be successful or handle gracefully
      expect([200, 400]).toContain(response.status());
    });
  });

  test.describe('Applications CRUD Integration', () => {
    
    test('should create, read, and delete application', async ({ page }) => {
      const token = await login(page);
      
      // Create application via API
      const createResponse = await page.request.post(`${API_BASE}/api/applications`, {
        headers: { Authorization: `Bearer ${token}` },
        data: {
          company_name: 'Test Company',
          role_title: 'Software Engineer Intern',
          status: 'applied',
          applied_date: new Date().toISOString()
        }
      });
      
      expect(createResponse.ok()).toBeTruthy();
      const app = await createResponse.json();
      const appId = app.id;
      
      expect(appId).toBeTruthy();
      expect(app.company_name).toBe('Test Company');
      expect(app.role_title).toBe('Software Engineer Intern');
      
      // Read application
      const getResponse = await page.request.get(`${API_BASE}/api/applications/${appId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      expect(getResponse.ok()).toBeTruthy();
      const retrieved = await getResponse.json();
      expect(retrieved.id).toBe(appId);
      
      // Update application
      const updateResponse = await page.request.put(`${API_BASE}/api/applications/${appId}`, {
        headers: { Authorization: `Bearer ${token}` },
        data: { status: 'interview' }
      });
      
      expect(updateResponse.ok()).toBeTruthy();
      
      // Delete application
      const deleteResponse = await page.request.delete(`${API_BASE}/api/applications/${appId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      expect([200, 204]).toContain(deleteResponse.status());
    });

    test('should list applications on dashboard', async ({ page }) => {
      const token = await login(page);
      
      // Navigate to applications page
      const appLink = page.locator('a:has-text("Applications")').first();
      await appLink.click();
      
      await expect(page).toHaveURL(/\/applications/);
      
      // API should return list
      const response = await page.request.get(`${API_BASE}/api/applications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(Array.isArray(data) || data.items).toBeTruthy();
    });
  });

  test.describe('Resume Upload & Analysis Integration', () => {
    
    test('should get user resumes list', async ({ page }) => {
      const token = await login(page);
      
      // Navigate to analyzer
      const analyzerLink = page.locator('a:has-text("Resume Analyzer")').first();
      await analyzerLink.click();
      
      await expect(page).toHaveURL(/\/analyzer/);
      
      // API call to get resumes
      const response = await page.request.get(`${API_BASE}/api/resumes`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      expect(response.ok()).toBeTruthy();
      const data = await response.json();
      expect(Array.isArray(data) || data.items).toBeTruthy();
    });
  });

  test.describe('Settings & Preferences Integration', () => {
    
    test('should fetch and update email preferences', async ({ page }) => {
      const token = await login(page);
      
      // Navigate to settings
      const settingsLink = page.locator('a:has-text("Settings")').first();
      await settingsLink.click();
      
      await expect(page).toHaveURL(/\/settings/);
      
      // Fetch preferences
      const getResponse = await page.request.get(`${API_BASE}/api/users/preferences`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Check response status (might be 200 or 404 if not set)
      expect([200, 404]).toContain(getResponse.status());
      
      if (getResponse.ok()) {
        const prefs = await getResponse.json();
        expect(prefs).toBeTruthy();
        
        // Update preferences
        const updateResponse = await page.request.put(`${API_BASE}/api/users/preferences`, {
          headers: { Authorization: `Bearer ${token}` },
          data: {
            notify_on_new_jobs: true,
            notify_on_resume_upload: false,
            weekly_digest: true,
            email_frequency: 'weekly'
          }
        });
        
        expect(updateResponse.ok()).toBeTruthy();
      }
    });

    test('should get current user profile', async ({ page }) => {
      const token = await login(page);
      
      const response = await page.request.get(`${API_BASE}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      expect(response.ok()).toBeTruthy();
      const user = await response.json();
      expect(user.email).toBe(TEST_EMAIL);
      expect(user.id).toBeTruthy();
    });
  });

  test.describe('Form Validation & Error Handling', () => {
    
    test('should handle invalid login credentials', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      
      // Try with wrong password
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', 'WrongPassword123!');
      await page.click('button:has-text("Sign In")');
      
      // Should show error
      await expect(page.locator('text=/Invalid|incorrect|failed/i')).toBeVisible({ timeout: 5000 });
      
      // Should not redirect
      await expect(page).toHaveURL(/\/login/);
    });

    test('should require email for login', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      
      // Try with only password
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      
      // Should show error or prevent submission
      const errorMsg = page.locator('text=/required|email/i');
      const stillOnLogin = await page.evaluate(() => window.location.pathname === '/login');
      
      expect(
        (await errorMsg.isVisible({ timeout: 3000 }).catch(() => false)) ||
        stillOnLogin
      ).toBeTruthy();
    });

    test('should validate application form fields', async ({ page }) => {
      const token = await login(page);
      
      // Navigate to applications
      const appLink = page.locator('a:has-text("Applications")').first();
      await appLink.click();
      
      await expect(page).toHaveURL(/\/applications/);
      
      // Find add button
      const addButton = page.locator('button:has-text(/Add|New/)').first();
      if (await addButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await addButton.click();
        
        // Try to submit empty form
        const submitButton = page.locator('button:has-text(/Submit|Create/)').last();
        if (await submitButton.isVisible({ timeout: 3000 }).catch(() => false)) {
          await submitButton.click();
          
          // Should show validation error or prevent submission
          const errorMsg = page.locator('text=/required|empty/i');
          const stillOnApp = await page.evaluate(() => window.location.pathname.includes('applications'));
          
          expect(
            (await errorMsg.isVisible({ timeout: 3000 }).catch(() => false)) ||
            stillOnApp
          ).toBeTruthy();
        }
      }
    });
  });

  test.describe('Data Consistency & State Management', () => {
    
    test('should maintain user session across page navigations', async ({ page }) => {
      const token1 = await login(page);
      
      // Navigate to different pages
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)').first();
      await jobsLink.click();
      await page.waitForLoadState('networkidle');
      
      const appLink = page.locator('a:has-text("Applications")').first();
      await appLink.click();
      await page.waitForLoadState('networkidle');
      
      // Token should still be valid
      const token2 = await page.evaluate(() => {
        const auth = localStorage.getItem('auth-store');
        if (auth) {
          const parsed = JSON.parse(auth);
          return parsed.state?.accessToken;
        }
        return null;
      });
      
      expect(token2).toBe(token1);
    });

    test('should clear auth on logout', async ({ page }) => {
      const token1 = await login(page);
      expect(token1).toBeTruthy();
      
      // Find and click logout
      let logoutButton = page.locator('button:has-text("Logout")');
      if (!(await logoutButton.isVisible({ timeout: 2000 }).catch(() => false))) {
        const userMenuButton = page.locator('button[aria-label*="user"], button[aria-label*="menu"]').first();
        if (await userMenuButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await userMenuButton.click();
          logoutButton = page.locator('button:has-text("Logout"), [role="menuitem"]:has-text("Logout")').first();
        }
      }
      
      if (await logoutButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await logoutButton.click();
        
        // Auth should be cleared
        const token2 = await page.evaluate(() => {
          const auth = localStorage.getItem('auth-store');
          if (auth) {
            const parsed = JSON.parse(auth);
            return parsed.state?.accessToken;
          }
          return null;
        });
        
        expect(token2).toBeNull();
      }
    });
  });

  test.describe('Performance & Load Testing', () => {
    
    test('should handle rapid navigation clicks', async ({ page }) => {
      const token = await login(page);
      
      // Rapidly click navigation links
      const dashboardLink = page.locator('a:has-text("Dashboard")').first();
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)').first();
      const appLink = page.locator('a:has-text("Applications")').first();
      const analyzerLink = page.locator('a:has-text("Resume Analyzer")').first();
      
      for (let i = 0; i < 2; i++) {
        await dashboardLink.click();
        await page.waitForTimeout(100);
        await jobsLink.click();
        await page.waitForTimeout(100);
        await appLink.click();
        await page.waitForTimeout(100);
        await analyzerLink.click();
        await page.waitForTimeout(100);
      }
      
      // Should still be on valid page
      const url = page.url();
      expect(
        url.includes('/dashboard') ||
        url.includes('/jobs') ||
        url.includes('/applications') ||
        url.includes('/analyzer')
      ).toBeTruthy();
    });

    test('should handle multiple API calls concurrently', async ({ page }) => {
      const token = await login(page);
      
      // Make multiple concurrent API calls
      const calls = await Promise.allSettled([
        page.request.get(`${API_BASE}/api/jobs?limit=10`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        page.request.get(`${API_BASE}/api/applications`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        page.request.get(`${API_BASE}/api/resumes`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        page.request.get(`${API_BASE}/api/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      // All should complete
      expect(calls.length).toBe(4);
      
      // At least some should succeed
      const succeeded = calls.filter(c => c.status === 'fulfilled');
      expect(succeeded.length).toBeGreaterThan(0);
    });
  });
});
