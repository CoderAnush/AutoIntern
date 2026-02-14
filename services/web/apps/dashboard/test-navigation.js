#!/usr/bin/env node
/**
 * Manual Navigation Test
 * Tests all pages after simulated login
 */

const axios = require('axios');

const BASE_URL = 'http://localhost:3000';
const API_URL = 'http://localhost:8000';
const TEST_EMAIL = 'test@example.com';
const TEST_PASSWORD = 'TestPass123!';

// Test configuration
const PAGES = [
  { name: 'Dashboard', url: '/', description: 'Home page with statistics' },
  { name: 'Find Jobs', url: '/jobs', description: 'Job listings page' },
  { name: 'Resume Analyzer', url: '/analyzer', description: 'Resume upload and analysis' },
  { name: 'Applications', url: '/applications', description: 'Application tracking kanban' },
  { name: 'AI Assistant', url: '/assistant', description: 'AI career guidance chat' },
  { name: 'Settings', url: '/settings', description: 'User preferences and settings' }
];

// Create axios instances
const webClient = axios.create({ baseURL: BASE_URL, maxRedirects: 5 });
const apiClient = axios.create({ baseURL: API_URL });

let authToken = null;

// Color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(color, message) {
  console.log(`${color}${message}${colors.reset}`);
}

async function testLogin() {
  log(colors.cyan, '\n════════════════════════════════════════');
  log(colors.cyan, '🔐 STEP 1: Testing Authentication');
  log(colors.cyan, '════════════════════════════════════════');

  try {
    log(colors.blue, `\nAttempting login with: ${TEST_EMAIL}`);
    
    const response = await apiClient.post('/api/auth/login', {
      email: TEST_EMAIL,
      password: TEST_PASSWORD
    });

    if (response.data.access_token) {
      authToken = response.data.access_token;
      log(colors.green, '✅ Login successful!');
      log(colors.green, `   Token: ${authToken.substring(0, 30)}...`);
      return true;
    } else {
      log(colors.red, '❌ Login failed: No token received');
      return false;
    }
  } catch (error) {
    log(colors.red, `❌ Login error: ${error.response?.data?.detail || error.message}`);
    return false;
  }
}

async function testFrontendHealth() {
  log(colors.cyan, '\n════════════════════════════════════════');
  log(colors.cyan, '🌐 STEP 2: Testing Frontend Availability');
  log(colors.cyan, '════════════════════════════════════════');

  try {
    const response = await webClient.get('/');
    if (response.status === 200) {
      log(colors.green, '✅ Frontend responding (status 200)');
      return true;
    } else {
      log(colors.yellow, `⚠️  Frontend returned status ${response.status}`);
      return true;
    }
  } catch (error) {
    log(colors.red, `❌ Frontend error: ${error.message}`);
    return false;
  }
}

async function testPageLoads() {
  log(colors.cyan, '\n════════════════════════════════════════');
  log(colors.cyan, '📄 STEP 3: Testing Navigation Pages');
  log(colors.cyan, '════════════════════════════════════════');

  let passCount = 0;
  let failCount = 0;

  for (const page of PAGES) {
    try {
      log(colors.blue, `\n📍 Testing: ${page.name}`);
      log(colors.blue, `   URL: ${page.url}`);
      log(colors.blue, `   Description: ${page.description}`);

      const response = await webClient.get(page.url, {
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {}
      });

      if (response.status === 200) {
        log(colors.green, `✅ Page loads successfully (status 200)`);
        
        // Check for common page indicators
        const content = response.data.toLowerCase();
        if (content.includes('next.element') || content.includes('root')) {
          log(colors.green, `   ✓ Has React app content`);
        }
        passCount++;
      } else {
        log(colors.yellow, `⚠️  Page returned status ${response.status}`);
        failCount++;
      }
    } catch (error) {
      if (error.response?.status === 404) {
        log(colors.red, `❌ Page not found (404)`);
      } else if (error.code === 'ECONNREFUSED') {
        log(colors.red, `❌ Cannot connect to frontend`);
      } else {
        log(colors.red, `❌ Error: ${error.message}`);
      }
      failCount++;
    }
  }

  log(colors.cyan, `\n   Summary: ${passCount} passed, ${failCount} failed`);
  return failCount === 0;
}

async function testAPIEndpoints() {
  log(colors.cyan, '\n════════════════════════════════════════');
  log(colors.cyan, '🔌 STEP 4: Testing Backend API Endpoints');
  log(colors.cyan, '════════════════════════════════════════');

  const endpoints = [
    { method: 'GET', url: '/api/jobs', name: 'Jobs List' },
    { method: 'GET', url: '/api/applications', name: 'Applications List' },
    { method: 'GET', url: '/api/resumes', name: 'Resumes List' },
    { method: 'GET', url: '/api/auth/users/preferences', name: 'User Preferences' },
    { method: 'GET', url: '/api/auth/me', name: 'User Profile' }
  ];

  let passCount = 0;
  let failCount = 0;

  for (const endpoint of endpoints) {
    try {
      log(colors.blue, `\n📍 Testing: ${endpoint.name}`);
      log(colors.blue, `   ${endpoint.method} ${endpoint.url}`);

      const config = authToken ? {
        headers: { Authorization: `Bearer ${authToken}` }
      } : {};

      let response;
      if (endpoint.method === 'GET') {
        response = await apiClient.get(endpoint.url, config);
      }

      if (response?.status === 200) {
        log(colors.green, `✅ API endpoint working (status 200)`);
        if (response.data) {
          console.log(`   Response preview: ${JSON.stringify(response.data).substring(0, 80)}...`);
        }
        passCount++;
      }
    } catch (error) {
      if (error.response?.status === 401) {
        log(colors.yellow, `⚠️  Unauthorized (may need auth)`);
      } else if (error.response?.status === 404) {
        log(colors.red, `❌ Endpoint not found (404)`);
      } else {
        log(colors.red, `❌ Error: ${error.message}`);
      }
      failCount++;
    }
  }

  log(colors.cyan, `\n   Summary: ${passCount} passed, ${failCount} failed`);
  return failCount === 0;
}

async function testSessionPersistence() {
  log(colors.cyan, '\n════════════════════════════════════════');
  log(colors.cyan, '🔐 STEP 5: Testing Session Persistence');
  log(colors.cyan, '════════════════════════════════════════');

  try {
    log(colors.blue, '\nVerifying user can access protected resources with token...');

    if (!authToken) {
      log(colors.yellow, '⚠️  No auth token available to test');
      return false;
    }

    const response = await apiClient.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${authToken}` }
    });

    if (response.status === 200 && response.data.email) {
      log(colors.green, `✅ Session valid for user: ${response.data.email}`);
      return true;
    }
  } catch (error) {
    log(colors.red, `❌ Session test failed: ${error.message}`);
    return false;
  }
}

async function runTests() {
  log(colors.cyan, '\n' + '═'.repeat(50));
  log(colors.cyan, 'AUTOINTERN - COMPLETE NAVIGATION TEST SUITE');
  log(colors.cyan, '═'.repeat(50));
  
  const startTime = Date.now();

  // Run tests in sequence
  const tests = [
    { name: 'Login', fn: testLogin },
    { name: 'Frontend Health', fn: testFrontendHealth },
    { name: 'Page Loads', fn: testPageLoads },
    { name: 'API Endpoints', fn: testAPIEndpoints },
    { name: 'Session Persistence', fn: testSessionPersistence }
  ];

  const results = [];
  for (const test of tests) {
    const result = await test.fn();
    results.push({ name: test.name, passed: result });
  }

  // Summary
  log(colors.cyan, '\n════════════════════════════════════════');
  log(colors.cyan, '📊 TEST SUMMARY');
  log(colors.cyan, '════════════════════════════════════════');

  const totalTests = results.length;
  const passedTests = results.filter(r => r.passed).length;
  const failedTests = totalTests - passedTests;

  results.forEach(r => {
    const status = r.passed ? `${colors.green}✅ PASS` : `${colors.red}❌ FAIL`;
    console.log(`${status}${colors.reset} - ${r.name}`);
  });

  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  log(colors.cyan, `\nTotal: ${passedTests}/${totalTests} tests passed (${duration}s)`);

  if (failedTests === 0) {
    log(colors.green, '\n🎉 ALL TESTS PASSED! The application is working correctly.');
  } else {
    log(colors.yellow, `\n⚠️  ${failedTests} test(s) failed. Check details above.`);
  }

  log(colors.cyan, '════════════════════════════════════════\n');

  return failedTests === 0;
}

// Run tests
runTests()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    log(colors.red, `\n❌ Test suite error: ${error.message}`);
    process.exit(1);
  });
