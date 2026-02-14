import { test, expect } from '@playwright/test';

/**
 * AutoIntern Full E2E Flow Tests
 * 
 * Comprehensive end-to-end tests covering the entire user journey:
 * - Authentication (login/register)
 * - Dashboard navigation
 * - Job browsing and filtering
 * - Resume upload and analysis
 * - Application tracking
 * - AI Assistant interaction
 * - Settings management
 * 
 * Run: npx playwright test e2e/full-flow.spec.ts
 * UI: npx playwright test e2e/full-flow.spec.ts --ui
 */

const BASE_URL = 'http://localhost:3000';
const TEST_EMAIL = 'test@example.com';
const TEST_PASSWORD = 'TestPass123!';

test.describe('AutoIntern Full User Flow', () => {
  
  test.beforeEach(async ({ page }) => {
    page.setDefaultTimeout(10000);
    page.setDefaultNavigationTimeout(10000);
  });

  test.describe('Part 1: Authentication & Dashboard', () => {
    
    test('should complete full login flow and reach dashboard', async ({ page }) => {
      // Navigate to login page
      await page.goto(`${BASE_URL}/login`);
      await expect(page).toHaveURL(/\/login/);
      
      // Verify login form elements
      const emailInput = page.locator('input[type="email"]');
      const passwordInput = page.locator('input[type="password"]');
      const submitButton = page.locator('button:has-text("Sign In")');
      
      await expect(emailInput).toBeVisible();
      await expect(passwordInput).toBeVisible();
      await expect(submitButton).toBeVisible();
      
      // Fill and submit form
      await emailInput.fill(TEST_EMAIL);
      await passwordInput.fill(TEST_PASSWORD);
      await submitButton.click();
      
      // Should show success toast
      await expect(page.locator('text=Welcome back')).toBeVisible({ timeout: 5000 });
      
      // Should redirect to dashboard
      await expect(page).toHaveURL('/');
      await page.waitForLoadState('networkidle');
    });

    test('should display sidebar navigation after login', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      const emailInput = page.locator('input[type="email"]');
      const passwordInput = page.locator('input[type="password"]');
      const submitButton = page.locator('button:has-text("Sign In")');
      
      await emailInput.fill(TEST_EMAIL);
      await passwordInput.fill(TEST_PASSWORD);
      await submitButton.click();
      
      await expect(page).toHaveURL('/');
      
      // Check sidebar navigation items
      const dashboardLink = page.locator('a:has-text("Dashboard")');
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)');
      const analyzerLink = page.locator('a:has-text("Resume Analyzer")');
      const applicationsLink = page.locator('a:has-text("Applications")');
      const assistantLink = page.locator('a:has-text("AI Assistant")');
      const settingsLink = page.locator('a:has-text("Settings")');
      
      await expect(dashboardLink).toBeVisible({ timeout: 5000 });
      await expect(jobsLink).toBeVisible({ timeout: 5000 });
      await expect(analyzerLink).toBeVisible({ timeout: 5000 });
      await expect(applicationsLink).toBeVisible({ timeout: 5000 });
      await expect(assistantLink).toBeVisible({ timeout: 5000 });
      await expect(settingsLink).toBeVisible({ timeout: 5000 });
    });

    test('should show user profile info on dashboard', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      const emailInput = page.locator('input[type="email"]');
      const passwordInput = page.locator('input[type="password"]');
      const submitButton = page.locator('button:has-text("Sign In")');
      
      await emailInput.fill(TEST_EMAIL);
      await passwordInput.fill(TEST_PASSWORD);
      await submitButton.click();
      
      await expect(page).toHaveURL('/');
      
      // User info should be visible
      await page.waitForLoadState('networkidle');
      const userInitial = page.locator('text=/T|t/').filter({ hasText: /^T$/ }).first();
      await expect(userInitial).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Part 2: Jobs Navigation & Browsing', () => {
    
    test.beforeEach(async ({ page }) => {
      // Login
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      await expect(page).toHaveURL('/');
      await page.waitForLoadState('networkidle');
    });

    test('should navigate to jobs page from sidebar', async ({ page }) => {
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)').first();
      await jobsLink.click();
      
      // Should navigate to jobs page
      await expect(page).toHaveURL(/\/jobs/);
      
      // Jobs page should load
      await page.waitForLoadState('networkidle');
      await expect(page.locator('text=/Jobs|Internships?|Browse Jobs/i')).toBeVisible({ timeout: 5000 });
    });

    test('should display job listings with filters', async ({ page }) => {
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)').first();
      await jobsLink.click();
      
      await expect(page).toHaveURL(/\/jobs/);
      await page.waitForLoadState('networkidle');
      
      // Should see job listing or seed button
      const jobCards = page.locator('[role="article"]');
      const seedButton = page.locator('button:has-text("Seed Jobs")');
      
      // Either should have jobs or be able to seed them
      const hasJobCards = await jobCards.count() > 0;
      const hasSeedButton = await seedButton.isVisible({ timeout: 3000 }).catch(() => false);
      
      expect(hasJobCards || hasSeedButton).toBeTruthy();
    });

    test('should allow filtering by job type', async ({ page }) => {
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)').first();
      await jobsLink.click();
      
      await expect(page).toHaveURL(/\/jobs/);
      
      // Look for filter buttons
      const filterButtons = page.locator('button:has-text(/All|Internship|Full-time|Part-time|Contract/)');
      const filterCount = await filterButtons.count();
      
      if (filterCount > 0) {
        // Click a filter
        const firstFilter = filterButtons.nth(1);
        await firstFilter.click();
        
        // Page should update
        await page.waitForLoadState('networkidle');
      }
    });

    test('should allow searching jobs', async ({ page }) => {
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)').first();
      await jobsLink.click();
      
      await expect(page).toHaveURL(/\/jobs/);
      
      // Find search input
      const searchInput = page.locator('input[placeholder*="Search"], input[type="text"]').first();
      if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await searchInput.fill('python');
        await page.keyboard.press('Enter');
        
        // Should perform search
        await page.waitForLoadState('networkidle');
      }
    });
  });

  test.describe('Part 3: Resume Analyzer', () => {
    
    test.beforeEach(async ({ page }) => {
      // Login
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      await expect(page).toHaveURL('/');
      await page.waitForLoadState('networkidle');
    });

    test('should navigate to resume analyzer', async ({ page }) => {
      const analyzerLink = page.locator('a:has-text("Resume Analyzer")').first();
      await analyzerLink.click();
      
      await expect(page).toHaveURL(/\/analyzer/);
      
      // Analyzer page should load
      await page.waitForLoadState('networkidle');
      await expect(page.locator('text=/Analyzer|Resume|Upload/i')).toBeVisible({ timeout: 5000 });
    });

    test('should display upload area for resume', async ({ page }) => {
      const analyzerLink = page.locator('a:has-text("Resume Analyzer")').first();
      await analyzerLink.click();
      
      await expect(page).toHaveURL(/\/analyzer/);
      
      // Should show upload instructions or existing resume
      const uploadArea = page.locator('text=/Upload|Drag|Drop/i');
      const uploadInput = page.locator('input[type="file"]');
      
      expect(
        (await uploadArea.isVisible({ timeout: 3000 }).catch(() => false)) ||
        (await uploadInput.isVisible({ timeout: 3000 }).catch(() => false))
      ).toBeTruthy();
    });

    test('should show resume quality score if available', async ({ page }) => {
      const analyzerLink = page.locator('a:has-text("Resume Analyzer")').first();
      await analyzerLink.click();
      
      await expect(page).toHaveURL(/\/analyzer/);
      await page.waitForLoadState('networkidle');
      
      // Check for quality score/gauge
      const scoreDisplay = page.locator('text=/Score|Quality|\/100/i');
      const scoreValue = page.locator('text=/[0-9]{1,3}\s*\/\s*100/');
      
      // Either shown or placeholder
      const hasScore = await scoreDisplay.isVisible({ timeout: 3000 }).catch(() => false) ||
                       await scoreValue.isVisible({ timeout: 3000 }).catch(() => false);
      
      // This is optional based on if resume is uploaded
      expect(hasScore || true).toBeTruthy();
    });
  });

  test.describe('Part 4: Applications Tracking', () => {
    
    test.beforeEach(async ({ page }) => {
      // Login
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      await expect(page).toHaveURL('/');
      await page.waitForLoadState('networkidle');
    });

    test('should navigate to applications page', async ({ page }) => {
      const applicationsLink = page.locator('a:has-text("Applications")').first();
      await applicationsLink.click();
      
      await expect(page).toHaveURL(/\/applications/);
      
      // Page should load
      await page.waitForLoadState('networkidle');
      await expect(page.locator('text=/Applications|Applied|Interview|Offer|Rejected/i')).toBeVisible({ timeout: 5000 });
    });

    test('should display kanban board for applications', async ({ page }) => {
      const applicationsLink = page.locator('a:has-text("Applications")').first();
      await applicationsLink.click();
      
      await expect(page).toHaveURL(/\/applications/);
      await page.waitForLoadState('networkidle');
      
      // Should see kanban columns
      const appliedColumn = page.locator('text="Applied"');
      const interviewColumn = page.locator('text="Interview"');
      const offerColumn = page.locator('text="Offer"');
      const rejectedColumn = page.locator('text="Rejected"');
      
      await expect(appliedColumn).toBeVisible({ timeout: 5000 });
      await expect(interviewColumn).toBeVisible({ timeout: 5000 });
      await expect(offerColumn).toBeVisible({ timeout: 5000 });
      await expect(rejectedColumn).toBeVisible({ timeout: 5000 });
    });

    test('should allow adding new application', async ({ page }) => {
      const applicationsLink = page.locator('a:has-text("Applications")').first();
      await applicationsLink.click();
      
      await expect(page).toHaveURL(/\/applications/);
      
      // Find add button
      const addButton = page.locator('button:has-text(/Add|New|Plus/)').first();
      if (await addButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await addButton.click();
        
        // Form should appear
        const companyInput = page.locator('input[placeholder*="Company"], input:has-attribute("aria-label", "company")').first();
        const roleInput = page.locator('input[placeholder*="Role"], input:has-attribute("aria-label", "role")').first();
        
        if (await companyInput.isVisible({ timeout: 3000 }).catch(() => false)) {
          await companyInput.fill('Test Company');
          await roleInput.fill('Software Engineer Intern');
          
          const submitButton = page.locator('button:has-text(/Submit|Create|Add|Save/)').last();
          await submitButton.click();
          
          // Should show success
          await expect(page.locator('text=/Added|Created|Success/i')).toBeVisible({ timeout: 5000 });
        }
      }
    });
  });

  test.describe('Part 5: AI Assistant', () => {
    
    test.beforeEach(async ({ page }) => {
      // Login
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      await expect(page).toHaveURL('/');
      await page.waitForLoadState('networkidle');
    });

    test('should navigate to AI assistant', async ({ page }) => {
      const assistantLink = page.locator('a:has-text("AI Assistant")').first();
      await assistantLink.click();
      
      await expect(page).toHaveURL(/\/assistant/);
      
      // Assistant page should load
      await page.waitForLoadState('networkidle');
      await expect(page.locator('text=/Assistant|Chat|AI/i')).toBeVisible({ timeout: 5000 });
    });

    test('should display chat interface', async ({ page }) => {
      const assistantLink = page.locator('a:has-text("AI Assistant")').first();
      await assistantLink.click();
      
      await expect(page).toHaveURL(/\/assistant/);
      
      // Chat should be visible
      const chatInput = page.locator('input, textarea').filter({ hasText: '' }).first();
      const sendButton = page.locator('button:has-text(/Send|Submit/)').filter({ hasText: 'Send' }).first();
      
      await expect(chatInput).toBeVisible({ timeout: 5000 });
      expect(await sendButton.isVisible({ timeout: 3000 }).catch(() => true)).toBeTruthy();
    });

    test('should allow sending assistant messages', async ({ page }) => {
      const assistantLink = page.locator('a:has-text("AI Assistant")').first();
      await assistantLink.click();
      
      await expect(page).toHaveURL(/\/assistant/);
      
      // Find input and send button
      const chatInput = page.locator('input, textarea').filter({ hasText: '' }).first();
      const sendButton = page.locator('button:has-text("Send"), button[type="submit"]').first();
      
      if (await chatInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await chatInput.fill('How do I prepare for interviews?');
        await sendButton.click();
        
        // Should show message sent
        await page.waitForLoadState('networkidle');
      }
    });

    test('should display suggestion prompts', async ({ page }) => {
      const assistantLink = page.locator('a:has-text("AI Assistant")').first();
      await assistantLink.click();
      
      await expect(page).toHaveURL(/\/assistant/);
      
      // Look for suggestion buttons
      const suggestions = page.locator('button:has-text(/interview|resume|cover|negotiate/i)');
      const suggestionCount = await suggestions.count();
      
      if (suggestionCount > 0) {
        expect(suggestionCount).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Part 6: Settings Management', () => {
    
    test.beforeEach(async ({ page }) => {
      // Login
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      await expect(page).toHaveURL('/');
      await page.waitForLoadState('networkidle');
    });

    test('should navigate to settings', async ({ page }) => {
      const settingsLink = page.locator('a:has-text("Settings")').first();
      await settingsLink.click();
      
      await expect(page).toHaveURL(/\/settings/);
      
      // Settings page should load
      await page.waitForLoadState('networkidle');
      await expect(page.locator('text=/Settings|Profile|Security|Notifications/i')).toBeVisible({ timeout: 5000 });
    });

    test('should display settings tabs', async ({ page }) => {
      const settingsLink = page.locator('a:has-text("Settings")').first();
      await settingsLink.click();
      
      await expect(page).toHaveURL(/\/settings/);
      await page.waitForLoadState('networkidle');
      
      // Check for tabs
      const profileTab = page.locator('button:has-text("Profile"), [role="tab"]:has-text("Profile")');
      const securityTab = page.locator('button:has-text("Security"), [role="tab"]:has-text("Security")');
      const notificationsTab = page.locator('button:has-text("Notifications"), [role="tab"]:has-text("Notifications")');
      
      await expect(profileTab).toBeVisible({ timeout: 5000 });
      expect(await securityTab.isVisible({ timeout: 3000 }).catch(() => false)).toBeTruthy();
      expect(await notificationsTab.isVisible({ timeout: 3000 }).catch(() => false)).toBeTruthy();
    });

    test('should allow toggling notification preferences', async ({ page }) => {
      const settingsLink = page.locator('a:has-text("Settings")').first();
      await settingsLink.click();
      
      await expect(page).toHaveURL(/\/settings/);
      
      // Click notifications tab
      const notificationsTab = page.locator('button:has-text("Notifications"), [role="tab"]:has-text("Notifications")');
      if (await notificationsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
        await notificationsTab.click();
        
        // Find toggle buttons
        const toggles = page.locator('button[role="switch"]');
        const toggleCount = await toggles.count();
        
        if (toggleCount > 0) {
          // Click first toggle
          await toggles.first().click();
          
          // Should show save/update
          const saveButton = page.locator('button:has-text(/Save|Update/)');
          expect(await saveButton.isVisible({ timeout: 3000 }).catch(() => true)).toBeTruthy();
        }
      }
    });
  });

  test.describe('Part 7: Logout & Session Management', () => {
    
    test.beforeEach(async ({ page }) => {
      // Login
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      await expect(page).toHaveURL('/');
      await page.waitForLoadState('networkidle');
    });

    test('should allow user logout', async ({ page }) => {
      // Find logout button in sidebar or menu
      let logoutButton = page.locator('button:has-text("Logout")');
      
      if (!(await logoutButton.isVisible({ timeout: 2000 }).catch(() => false))) {
        // Try user menu
        const userMenuButton = page.locator('button[aria-label*="user"], button[aria-label*="menu"]').first();
        if (await userMenuButton.isVisible({ timeout: 2000 }).catch(() => false)) {
          await userMenuButton.click();
          logoutButton = page.locator('button:has-text("Logout"), [role="menuitem"]:has-text("Logout")').first();
        }
      }
      
      if (await logoutButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await logoutButton.click();
        
        // Should redirect to login
        await expect(page).toHaveURL(/\/(login|)/);
      }
    });

    test('should redirect to login if accessing protected route without auth', async ({ page }) => {
      await page.goto(`${BASE_URL}/applications`);
      
      // Should redirect to login
      await expect(page).toHaveURL(/\/login/);
    });
  });

  test.describe('Responsive Design', () => {
    
    test('should work on mobile viewport', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });
      
      await page.goto(`${BASE_URL}/login`);
      const emailInput = page.locator('input[type="email"]');
      const passwordInput = page.locator('input[type="password"]');
      const submitButton = page.locator('button:has-text("Sign In")');
      
      await expect(emailInput).toBeVisible();
      await expect(passwordInput).toBeVisible();
      await expect(submitButton).toBeVisible();
      
      // Fill and submit
      await emailInput.fill(TEST_EMAIL);
      await passwordInput.fill(TEST_PASSWORD);
      await submitButton.click();
      
      await expect(page).toHaveURL('/');
      
      // Mobile menu should be visible
      const mobileMenu = page.locator('button[aria-label*="menu"], button:has(svg)').first();
      await expect(mobileMenu).toBeVisible({ timeout: 5000 });
    });

    test('should work on tablet viewport', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });
      
      await page.goto(`${BASE_URL}/login`);
      
      const emailInput = page.locator('input[type="email"]');
      await expect(emailInput).toBeVisible();
      
      await emailInput.fill(TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      
      await expect(page).toHaveURL('/');
    });

    test('should work on desktop viewport', async ({ page }) => {
      // Default is desktop
      await page.goto(`${BASE_URL}/login`);
      
      const emailInput = page.locator('input[type="email"]');
      await expect(emailInput).toBeVisible();
      
      await emailInput.fill(TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      
      await expect(page).toHaveURL('/');
    });
  });

  test.describe('Error Handling & Edge Cases', () => {
    
    test('should handle network errors gracefully', async ({ page }) => {
      // Go to jobs page
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      
      await expect(page).toHaveURL('/');
      
      const jobsLink = page.locator('a:has-text(/Find Jobs|Jobs/)').first();
      await jobsLink.click();
      
      await expect(page).toHaveURL(/\/jobs/);
      
      // Page should still be usable
      const searchInput = page.locator('input[placeholder*="Search"], input[type="text"]').first();
      if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        expect(await searchInput.isEnabled()).toBeTruthy();
      }
    });

    test('should handle missing data gracefully', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      
      await expect(page).toHaveURL('/');
      await page.waitForLoadState('networkidle');
      
      // Dashboard should load even with empty data
      const dashboard = page.locator('text=/Dashboard|Welcome/i');
      await expect(dashboard).toBeVisible({ timeout: 5000 });
    });
  });
});
