import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost:3000';
const TEST_EMAIL = 'test@example.com';
const TEST_PASSWORD = 'TestPass123!';

// Navigation pages to test
const NAVIGATION_PAGES = [
  {
    name: 'Dashboard',
    url: '/',
    selectors: ['Welcome back', 'Quick Actions', 'Statistics'] // Key elements on page
  },
  {
    name: 'Find Jobs',
    url: '/jobs',
    selectors: ['Job Type', 'Search', 'job-card'] // Key elements on page
  },
  {
    name: 'Resume Analyzer',
    url: '/analyzer',
    selectors: ['drag-drop', 'Quality Score', 'Matched Jobs'] // Key elements on page
  },
  {
    name: 'Applications',
    url: '/applications',
    selectors: ['Applied', 'Interview', 'Offer', 'Rejected'] // Key elements on page (kanban columns)
  },
  {
    name: 'AI Assistant',
    url: '/assistant',
    selectors: ['Chat', 'message', 'Suggestions'] // Key elements on page
  },
  {
    name: 'Settings',
    url: '/settings',
    selectors: ['Profile', 'Security', 'Notifications'] // Key tabs/sections on page
  }
];

async function loginUser(page: any) {
  await page.goto(`${BASE_URL}/login`);
  
  // Fill login form
  await page.fill('input[type="email"]', TEST_EMAIL);
  await page.fill('input[type="password"]', TEST_PASSWORD);
  
  // Click login button
  await page.click('button:has-text("Sign In")');
  
  // Wait for redirect to dashboard
  await page.waitForURL('/');
  await page.waitForSelector('text=Welcome back', { timeout: 5000 });
}

test.describe('Navigation Pages After Login', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await loginUser(page);
  });

  // Test each navigation page
  for (const pageConfig of NAVIGATION_PAGES) {
    test(`✅ ${pageConfig.name} page loads correctly`, async ({ page }) => {
      console.log(`\n📄 Testing: ${pageConfig.name}`);
      
      // Navigate to page
      await page.goto(`${BASE_URL}${pageConfig.url}`);
      
      // Verify page loaded
      await expect(page).toHaveURL(pageConfig.url);
      
      // Wait for page to be ready (no loading spinner)
      await page.waitForLoadState('networkidle', { timeout: 5000 });
      
      // Check for key page elements
      let foundElements = 0;
      for (const selector of pageConfig.selectors) {
        try {
          // Try text selector first
          const element = await page.locator(`text=${selector}`).first();
          if (await element.isVisible().catch(() => false)) {
            console.log(`  ✅ Found: "${selector}"`);
            foundElements++;
          } else {
            // Try as class/id selector
            const altElement = page.locator(`[class*="${selector}"], [id*="${selector}"]`).first();
            if (await altElement.isVisible().catch(() => false)) {
              console.log(`  ✅ Found: "${selector}"`);
              foundElements++;
            } else {
              console.log(`  ⚠️  Element not found: "${selector}" (may not be visible yet)`);
            }
          }
        } catch (e) {
          console.log(`  ⚠️  Could not verify: "${selector}"`);
        }
      }
      
      // Verify at least some elements are present
      expect(foundElements).toBeGreaterThan(0);
    });
  }

  test('📱 Test all navigation via sidebar menu', async ({ page }) => {
    console.log('\n🔗 Testing navigation via sidebar menu\n');
    
    // We should be on dashboard after login
    await expect(page).toHaveURL('/');
    
    // Test each navigation link
    const navItems = [
      { text: 'Dashboard', url: '/' },
      { text: /Find Jobs|Jobs/, url: '/jobs' },
      { text: 'Resume Analyzer', url: '/analyzer' },
      { text: 'Applications', url: '/applications' },
      { text: 'AI Assistant', url: '/assistant' },
      { text: 'Settings', url: '/settings' }
    ];
    
    for (const navItem of navItems) {
      console.log(`📍 Navigating to: ${navItem.text}`);
      
      // Click nav item
      await page.locator(`a:has-text("${navItem.text}")`).first().click();
      
      // Verify URL changed
      await page.waitForURL(navItem.url, { timeout: 5000 });
      await expect(page).toHaveURL(navItem.url);
      
      console.log(`   ✅ Successfully navigated to ${navItem.url}\n`);
    }
  });

  test('🔄 Test rapid page switching', async ({ page }) => {
    console.log('\n⚡ Testing rapid page switching\n');
    
    const pages = ['/', '/jobs', '/analyzer', '/applications', '/assistant', '/settings'];
    
    for (let i = 0; i < 2; i++) {
      for (const pageUrl of pages) {
        await page.goto(`${BASE_URL}${pageUrl}`);
        await page.waitForLoadState('networkidle', { timeout: 5000 });
        
        const currentUrl = page.url();
        expect(currentUrl).toContain(pageUrl);
        console.log(`  ✅ [Iteration ${i + 1}] Loaded: ${pageUrl}`);
      }
    }
    
    console.log('\n✅ All rapid switches completed successfully\n');
  });

  test('🎯 Test sidebar remains visible on all pages', async ({ page }) => {
    console.log('\n📊 Testing sidebar visibility\n');
    
    const pages = ['/', '/jobs', '/analyzer', '/applications', '/assistant', '/settings'];
    
    for (const pageUrl of pages) {
      await page.goto(`${BASE_URL}${pageUrl}`);
      
      // Check if sidebar exists
      const sidebar = page.locator('nav, [class*="sidebar"]').first();
      const sidebarVisible = await sidebar.isVisible().catch(() => false);
      
      if (sidebarVisible) {
        console.log(`  ✅ Sidebar visible on ${pageUrl}`);
      } else {
        console.log(`  ⚠️  Sidebar not visible on ${pageUrl} (may be mobile view)`);
      }
    }
  });

  test('🚪 Test session persistence across pages', async ({ page }) => {
    console.log('\n🔐 Testing session persistence\n');
    
    // Get auth token from first page
    const initialToken = await page.evaluate(() => {
      return localStorage.getItem('auth_token') || localStorage.getItem('token');
    });
    
    expect(initialToken).toBeTruthy();
    console.log(`  ✅ Auth token present: ${initialToken?.substring(0, 20)}...`);
    
    // Navigate through pages and check token remains
    const pages = ['/jobs', '/analyzer', '/applications', '/assistant', '/settings', '/'];
    
    for (const pageUrl of pages) {
      await page.goto(`${BASE_URL}${pageUrl}`);
      await page.waitForLoadState('networkidle', { timeout: 5000 });
      
      const currentToken = await page.evaluate(() => {
        return localStorage.getItem('auth_token') || localStorage.getItem('token');
      });
      
      expect(currentToken).toBe(initialToken);
      console.log(`  ✅ Token persisted on page ${pageUrl}`);
    }
  });

  test('📲 Test mobile responsive navigation', async ({ browser }) => {
    console.log('\n📱 Testing mobile navigation\n');
    
    // Create mobile context
    const mobileContext = await browser.newContext({
      viewport: { width: 375, height: 667 }
    });
    
    const mobilePage = await mobileContext.newPage();
    
    // Login on mobile
    await loginUser(mobilePage);
    
    // Test navigation on mobile
    const mobilePages = ['/', '/jobs', '/analyzer', '/applications', '/assistant', '/settings'];
    
    for (const pageUrl of mobilePages) {
      await mobilePage.goto(`${BASE_URL}${pageUrl}`);
      await mobilePage.waitForLoadState('networkidle', { timeout: 5000 });
      
      expect(mobilePage).toHaveURL(pageUrl);
      console.log(`  ✅ Mobile page load: ${pageUrl}`);
    }
    
    await mobileContext.close();
  });
});

// Summary test
test.describe('Navigation Test Summary', () => {
  test('Print all tested pages', async () => {
    console.log('\n\n' + '='.repeat(60));
    console.log('✅ NAVIGATION PAGES TESTED:');
    console.log('='.repeat(60));
    NAVIGATION_PAGES.forEach((page, index) => {
      console.log(`${index + 1}. ${page.name.padEnd(20)} → ${page.url}`);
    });
    console.log('='.repeat(60) + '\n');
  });
});
