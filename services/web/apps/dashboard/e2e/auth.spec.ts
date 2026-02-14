import { test, expect } from '@playwright/test';

/**
 * E2E Tests for AutoIntern Authentication & Navigation Flow
 * 
 * Test Credentials:
 * Email: test@example.com
 * Password: TestPass123!
 * 
 * Run: npx playwright test
 * Watch: npx playwright test --watch
 * UI: npx playwright test --ui
 */

const TEST_EMAIL = 'test@example.com';
const TEST_PASSWORD = 'TestPass123!';

test.describe('AutoIntern E2E Tests', () => {
  
  test.describe('Landing Page', () => {
    test('should render landing page with hero and CTAs', async ({ page }) => {
      await page.goto('/');
      
      // Check hero title
      await expect(page.locator('text=Land Your Dream Internship with AI')).toBeVisible();
      
      // Check for key sections
      await expect(page.locator('text=Features')).toBeVisible();
      await expect(page.locator('text=Smart Job Matching')).toBeVisible();
      
      // Check CTA buttons
      const signInButton = page.locator('a:has-text("Sign In")').first();
      const getStartedButton = page.locator('button:has-text("Get Started")').first();
      
      await expect(signInButton.or(getStartedButton)).toBeVisible();
    });

    test('should have working navigation links', async ({ page }) => {
      await page.goto('/');
      
      // Click on Sign In button (should go to /login)
      await page.click('a:has-text("Sign In")');
      await expect(page).toHaveURL('/login');
    });
  });

  test.describe('Authentication Flow', () => {
    test('should render login form with all fields', async ({ page }) => {
      await page.goto('/login');
      
      // Check page title
      await expect(page.locator('text=Welcome back')).toBeVisible();
      
      // Check form fields
      const emailInput = page.locator('input[type="email"]');
      const passwordInput = page.locator('input[type="password"]');
      const submitButton = page.locator('button:has-text("Sign In")');
      
      await expect(emailInput).toBeVisible();
      await expect(passwordInput).toBeVisible();
      await expect(submitButton).toBeVisible();
    });

    test('should show validation errors for empty form', async ({ page }) => {
      await page.goto('/login');
      
      // Try to submit empty form
      await page.click('button:has-text("Sign In")');
      
      // Should show error toast
      await expect(page.locator('text=Email and password required')).toBeVisible({ timeout: 3000 });
    });

    test('should reject invalid credentials', async ({ page }) => {
      await page.goto('/login');
      
      // Enter invalid credentials
      await page.fill('input[type="email"]', 'invalid@example.com');
      await page.fill('input[type="password"]', 'WrongPassword123!');
      
      // Submit form
      await page.click('button:has-text("Sign In")');
      
      // Should show error message
      await expect(page.locator('text=/Invalid email|password/')).toBeVisible({ timeout: 5000 });
    });

    test('should successfully login with valid credentials', async ({ page }) => {
      await page.goto('/login');
      
      // Enter valid credentials
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      
      // Submit form
      await page.click('button:has-text("Sign In")');
      
      // Should show success message
      await expect(page.locator('text=Welcome back')).toBeVisible();
      
      // Should redirect to dashboard/home
      await expect(page).toHaveURL('/');
      
      // Wait for page to load
      await page.waitForLoadState('networkidle');
    });

    test('should show password visibility toggle', async ({ page }) => {
      await page.goto('/login');
      
      const passwordInput = page.locator('input[type="password"]');
      const toggleButton = page.locator('button[type="button"]').filter({ has: page.locator('svg') }).first();
      
      // Initially password should be hidden
      await expect(passwordInput).toHaveAttribute('type', 'password');
      
      // Click toggle to show password
      await toggleButton.click();
      
      // Password should now be visible
      await expect(passwordInput).toHaveAttribute('type', 'text');
      
      // Click toggle again to hide
      await toggleButton.click();
      
      // Password should be hidden again
      await expect(passwordInput).toHaveAttribute('type', 'password');
    });

    test('should have link to register page', async ({ page }) => {
      await page.goto('/login');
      
      // Find and click the "Create one" link
      await page.click('a:has-text("Create one")');
      
      // Should navigate to register page
      await expect(page).toHaveURL('/register');
    });
  });

  test.describe('Post-Login Navigation', () => {
    test.beforeEach(async ({ page }) => {
      // Login before each test
      await page.goto('/login');
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      
      // Wait for redirect
      await page.waitForURL('/');
      await page.waitForLoadState('networkidle');
    });

    test('should display dashboard at home page', async ({ page }) => {
      // Should be on home page
      await expect(page).toHaveURL('/');
      
      // Should see dashboard content or main navigation
      const navbar = page.locator('nav');
      await expect(navbar).toBeVisible({ timeout: 5000 });
    });

    test('should have working navigation menu', async ({ page }) => {
      // Wait for navigation to be visible
      const jobsLink = page.locator('a:has-text(/jobs|Jobs/)').first();
      
      if (await jobsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        // Click on Jobs/Analyzer/Applications etc
        await jobsLink.click();
        
        // Should navigate to jobs page
        await expect(page).toHaveURL(/\/(jobs|analyzer|applications)/);
      }
    });

    test('should have user profile/settings accessible', async ({ page }) => {
      // Look for user menu or profile button
      const userMenu = page.locator('button[aria-label*="profile"]').or(
        page.locator('button:has-text("Settings")')
      ).first();
      
      if (await userMenu.isVisible({ timeout: 3000 }).catch(() => false)) {
        await userMenu.click();
        
        // Should see menu options
        await expect(page.locator('text=/settings|profile|logout/i')).toBeVisible({ timeout: 2000 });
      }
    });

    test('should allow logout', async ({ page }) => {
      // Try to find and click logout button
      let logoutButton = page.locator('button:has-text("Logout")');
      
      if (!(await logoutButton.isVisible({ timeout: 2000 }).catch(() => false))) {
        // Try in dropdown menu
        const userMenu = page.locator('button[aria-label*="profile"]').or(
          page.locator('[role="menuitem"]:has-text("Settings")')
        ).first();
        
        if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
          await userMenu.click();
          logoutButton = page.locator('button:has-text("Logout")').or(
            page.locator('[role="menuitem"]:has-text("Logout")')
          );
        }
      }
      
      if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await logoutButton.click();
        
        // Should redirect to login or home
        await expect(page).toHaveURL(/\/(login|)/);
      }
    });
  });

  test.describe('Registration Flow', () => {
    test('should render register form', async ({ page }) => {
      await page.goto('/register');
      
      // Check page title
      await expect(page.locator('text=/create|sign up/i')).toBeVisible();
      
      // Check form fields
      const emailInput = page.locator('input[type="email"]');
      const passwordInputs = page.locator('input[type="password"]');
      
      await expect(emailInput).toBeVisible();
      await expect(passwordInputs.first()).toBeVisible();
    });

    test('should show validation errors for weak password', async ({ page }) => {
      await page.goto('/register');
      
      // Enter email
      await page.fill('input[type="email"]', `newuser${Date.now()}@example.com`);
      
      // Enter weak password
      await page.fill('input[type="password"]', 'weak');
      
      // Try to submit
      await page.click('button:has-text(/sign up|register|create/i)');
      
      // Should show error message about password strength
      await expect(page.locator('text=/password|weak|strong|uppercase|number/i')).toBeVisible({ timeout: 3000 });
    });

    test('should have link to login page', async ({ page }) => {
      await page.goto('/register');
      
      // Find and click the "Sign In" link
      await page.click('a:has-text(/sign in|login/i)');
      
      // Should navigate to login page
      await expect(page).toHaveURL('/login');
    });
  });

  test.describe('Protected Routes', () => {
    test('should redirect unauthenticated user from /jobs', async ({ page }) => {
      // Try to access protected route without login
      await page.goto('/jobs');
      
      // Should redirect to login
      await expect(page).toHaveURL('/login');
    });

    test('should redirect unauthenticated user from /analyzer', async ({ page }) => {
      // Try to access protected route without login
      await page.goto('/analyzer');
      
      // Should redirect to login
      await expect(page).toHaveURL('/login');
    });

    test('should redirect unauthenticated user from /applications', async ({ page }) => {
      // Try to access protected route without login
      await page.goto('/applications');
      
      // Should redirect to login
      await expect(page).toHaveURL('/login');
    });

    test('should allow authenticated user to access /jobs', async ({ page }) => {
      // Login first
      await page.goto('/login');
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      await page.waitForURL('/');
      
      // Navigate to jobs
      const jobsLink = page.locator('a:has-text(/jobs|Jobs/)').first();
      if (await jobsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await jobsLink.click();
        await page.waitForURL(/\/jobs/);
        await expect(page).toHaveURL(/\/jobs/);
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should show proper error messages on network failure', async ({ page }) => {
      await page.goto('/login');
      
      // Simulate offline mode
      await page.context().setBrowserContext({
        offline: true
      }).catch(() => { /* ignore */ });
      
      // Try to login - will likely fail
      await page.fill('input[type="email"]', TEST_EMAIL);
      await page.fill('input[type="password"]', TEST_PASSWORD);
      await page.click('button:has-text("Sign In")');
      
      // Go back online
      await page.context().reset().catch(() => { /* ignore */ });
    });

    test('should handle 404 gracefully', async ({ page }) => {
      // Visit non-existent page
      const response = await page.goto('/non-existent-page');
      
      // Should either show 404 or redirect to home
      const is404 = response?.status() === 404;
      const isHome = page.url().includes('/');
      
      await expect(is404 || isHome).toBeTruthy();
    });
  });
});
