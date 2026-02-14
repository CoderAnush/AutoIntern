# AutoIntern Complete E2E Testing & Login Guide

## 📋 Overview

This guide provides step-by-step instructions to:
1. Start the PostgreSQL database
2. Seed test users
3. Start the backend API
4. Start the frontend
5. Run E2E tests (with Playwright)
6. Verify login flow in browser

---

## 🔑 Test Credentials

Use these credentials for testing:

| Email | Password | Purpose |
|-------|----------|---------|
| `test@example.com` | `TestPass123!` | Primary test user (for E2E) |
| `demo@autointern.com` | `DemoPass123!` | Demo account |
| `admin@autointern.com` | `AdminPass123!` | Admin test account |
| `john.doe@example.com` | `JohnDoe123!` | Sample user profile |
| `jane.smith@example.com` | `JaneSmith123!` | Sample user profile |

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

---

## 🚀 Quick Start (All Services)

### Option A: Using Docker Compose (Recommended)

```powershell
# From project root
cd AutoIntern

# Start all services (PostgreSQL, Redis, Elasticsearch, MinIO, API, Frontend)
docker-compose up -d

# Wait for services to be ready (30-60 seconds)
Start-Sleep -Seconds 30

# Seed test users
cd services/api
python seed_test_users.py

# Frontend should auto-start at http://localhost:3000
```

**Cleanup:**
```powershell
docker-compose down
```

---

## 🔧 Manual Setup (Step-by-Step)

### Step 1: Start PostgreSQL Database

**Windows (Docker):**
```powershell
# Pull and run PostgreSQL
docker run -d `
  --name autointern-postgres `
  -e POSTGRES_USER=autointern `
  -e POSTGRES_PASSWORD=change-me `
  -e POSTGRES_DB=autointern `
  -p 5432:5432 `
  postgres:15

# Wait for database to start
Start-Sleep -Seconds 5
```

**Windows (Local Installation):**
```powershell
# If PostgreSQL is installed locally
# Make sure it's running in Services (postgresql-x64-15)
Get-Service postgresql* | Start-Service
```

**Verify Connection:**
```powershell
# Test connection
psql -U autointern -d autointern -h localhost -w

# You should see: psql (15.x)
# Type: \q to exit
```

---

### Step 2: Start Redis (for Rate Limiting)

**Docker:**
```powershell
docker run -d `
  --name autointern-redis `
  -p 6379:6379 `
  redis:7

Start-Sleep -Seconds 3
```

---

### Step 3: Seed Test Users

```powershell
# Navigate to API directory
cd services/api

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run seeder script
python seed_test_users.py
```

**Expected Output:**
```
🌱 Starting test user seeding...
📊 Creating database schema...
✓ Schema created
✓ Created user: test@example.com
✓ Created user: demo@autointern.com
✓ Created user: admin@autointern.com
✓ Created user: john.doe@example.com
✓ Created user: jane.smith@example.com

✅ Test users seeded successfully!

============================================================
TEST CREDENTIALS FOR E2E TESTING
============================================================

📧 Email:    test@example.com
🔑 Password: TestPass123!
...
```

---

### Step 4: Start Backend API

```powershell
# From services/api
cd services/api

# Create .env if not exists (should already exist in AutoIntern/.env)
# Verify DATABASE_URL=postgresql+asyncpg://autointern:change-me@localhost:5432/autointern

# Install/update dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Test Backend:**
```powershell
# In another terminal
curl http://localhost:8000/health

# Should return:
# {"status":"healthy"}
```

---

### Step 5: Start Frontend

```powershell
# From services/web/apps/dashboard
cd services/web/apps/dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

**Expected Output:**
```
> next dev -p 3000
   ▲ Next.js 14.2.21
   - Local:        http://localhost:3000
   - Environments: .env.local

✓ Ready in 1234ms
```

**Frontend URL:** http://localhost:3000

---

## 🧪 Running E2E Tests

### Setup Playwright

```powershell
# From dashboard directory
cd services/web/apps/dashboard

# Install Playwright browsers
npx playwright install

# This downloads Chromium, Firefox, and WebKit (~500MB)
```

### Run Tests

**Full Test Suite:**
```powershell
npx playwright test
```

**Interactive UI Mode (Recommended):**
```powershell
npx playwright test --ui
```
- Opens interactive test runner
- Click tests to run individually
- See live execution
- Debug easily

**Watch Mode (Development):**
```powershell
npx playwright test --watch
```
- Auto-reruns tests on file changes
- Good for TDD workflow

**Run Specific Test:**
```powershell
npx playwright test e2e/auth.spec.ts
npx playwright test -g "should successfully login"
```

**Run on Specific Browser:**
```powershell
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

### View Test Results

```powershell
# Generate HTML report
npx playwright show-report
```

---

## 🌐 Manual Browser Testing

### Login & Navigation Test

1. **Open Frontend**
   - URL: http://localhost:3000

2. **Verify Landing Page**
   - Should see: "Land Your Dream Internship with AI"
   - Check: Hero section, Features, Pricing
   - Click "Sign In" button

3. **Test Login (Valid Credentials)**
   - **Email:** `test@example.com`
   - **Password:** `TestPass123!`
   - Click "Sign In"
   - Should see: Success toast "Welcome back!"
   - Should redirect to dashboard

4. **Verify Dashboard**
   - Check navigation menu appears
   - Look for: Jobs, Analyzer, Applications, Settings
   - Check user profile/settings accessible

5. **Test Navigation**
   - Click "Jobs" → Should go to /jobs
   - Click "Analyzer" → Should go to /analyzer
   - Click "Applications" → Should go to /applications
   - Click "Settings" → Should go to settings

6. **Test Logout (if implemented)**
   - Find user menu/profile button
   - Click "Logout"
   - Should redirect to login or home page

### Test Invalid Login

1. **Go to Login Page:** http://localhost:3000/login
2. **Enter Wrong Credentials:**
   - Email: `test@example.com`
   - Password: `WrongPassword123!`
3. **Should See Error:** Red toast with "Invalid email or password"

### Test Protected Routes

1. **Logout First** (or open in new incognito window)
2. **Try to Access Protected Route:**
   - URL: http://localhost:3000/jobs
   - Should redirect to /login
   - Repeat for /analyzer, /applications

---

## 📊 Verifying All Components

### Database Check

```powershell
# Connect to PostgreSQL
psql -U autointern -d autointern -h localhost

# List tables
\dt

# Expected output:
#           List of relations
# Schema |      Name      | Type  | Owner
#--------+----------------+-------+----------
# public | users          | table | autointern
# public | jobs           | table | autointern
# public | resumes        | table | autointern
# ...

# Check test users
SELECT id, email, is_active FROM users;

# Should show 5 test users
```

### Backend API Check

```powershell
# Health check
curl http://localhost:8000/health

# Register endpoint (post-login call)
curl -X GET http://localhost:8000/api/auth/register `
  -H "Content-Type: application/json"

# Login endpoint
curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'

# Expected response:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer",
#   "expires_in": 1800
# }
```

### Frontend Check

```powershell
# Open browser developer console (F12)
# Go to http://localhost:3000

# Check Console tab for errors
# Should see: No errors

# Check Network tab for API calls
# On login, should see POST /api/auth/login returning 200 OK
```

---

## 🐛 Troubleshooting

### "Database connection refused"

```powershell
# Check if PostgreSQL is running
docker ps | Select-String postgres

# If not running, start it
docker start autointern-postgres

# Or check PostgreSQL service
Get-Service postgresql* | Where-Object {$_.Status -eq "Stopped"} | Start-Service
```

### "Too many failed login attempts"

The system has account lockout protection:
- After 5 failed login attempts, account locked for 15 minutes
- Wait 15 minutes or use a different test user

### "CORS Error"

```
Access to XMLHttpRequest blocked by CORS policy
```

- Check `.env` CORS_ORIGINS setting
- Should include: `http://localhost:3000`

### "Backend not starting"

```powershell
# Check if Redis is UP
docker ps | Select-String redis

# Check for port conflicts
Get-NetTcpConnection -LocalPort 8000 -ErrorAction SilentlyContinue

# Kill process if needed
taskkill /PID <pid> /F

# Restart backend
```

### "Tests failing with "timeout"

```powershell
# Increase timeout in playwright.config.ts
use: {
    baseURL: 'http://localhost:3000',
    navigationTimeout: 30000,  # 30 seconds
}

# Or run tests slower
npx playwright test --update-snapshots
```

---

## ✅ Verification Checklist

- [ ] PostgreSQL running on `localhost:5432`
- [ ] Redis running on `localhost:6379`
- [ ] Backend API running on `http://localhost:8000`
- [ ] Frontend running on `http://localhost:3000`
- [ ] Test users created in database
- [ ] Landing page loads without errors
- [ ] Login form renders correctly
- [ ] Can login with `test@example.com` / `TestPass123!`
- [ ] After login, redirected to dashboard
- [ ] Navigation menu appears and is clickable
- [ ] Can navigate to /jobs, /analyzer, /applications
- [ ] E2E tests run successfully (`npx playwright test`)
- [ ] No console errors in browser DevTools

---

## 📚 API Endpoints Used by Frontend

### Auth Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create new account |
| POST | `/api/auth/login` | Login with email/password |
| GET | `/api/auth/me` | Get current user profile |
| POST | `/api/auth/change-password` | Change password |
| POST | `/api/auth/refresh-token` | Refresh access token |

### Protected Endpoints (require Bearer token)

All other endpoints require an `Authorization: Bearer <access_token>` header.

---

## 🎯 E2E Test Coverage

The Playwright test suite (`e2e/auth.spec.ts`) covers:

✅ **Landing Page Tests**
- Hero rendering
- Feature sections
- Navigation links

✅ **Login Tests**
- Form field validation
- Empty form submission
- Invalid credentials
- Valid credentials → redirect to dashboard
- Password visibility toggle
- Link to register page

✅ **Post-Login Navigation**
- Dashboard display
- Navigation menu
- Profile/settings access
- Logout functionality

✅ **Registration Tests**
- Form rendering
- Password validation
- Link to login page

✅ **Protected Routes**
- Unauthorized redirects to login
- Authenticated access allowed

✅ **Error Handling**
- Network failures
- 404 pages

---

## 📱 Mobile Testing

The E2E tests also run on mobile viewports:

```powershell
# Run mobile tests
npx playwright test --project="Mobile Chrome"
npx playwright test --project="Mobile Safari"
```

---

## 🔍 Debugging Tests

```powershell
# Debug mode with browser visible
npx playwright test --debug

# Run specific test with logging
npx playwright test e2e/auth.spec.ts --debug

# Generate trace for failed tests
npx playwright test --trace on
```

---

## 📝 Continuous Integration (CI)

To run tests in CI/CD pipeline:

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd services/web/apps/dashboard && npm install
      - run: npx playwright install --with-deps
      - run: npm run build
      - run: npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 💡 Tips & Best Practices

1. **Keep Browser DevTools Open** during manual testing to see API calls
2. **Use incognito window** to test unauthenticated flows
3. **Check network tab** to verify API responses
4. **Always clear localStorage** between test runs if debugging
5. **Use test:e2e:ui mode** for development and debugging
6. **Commit `.env.local`** variations to version control (with placeholder values)

---

## 📞 Getting Help

If you encounter issues:

1. Check **Terminal Output** for error messages
2. Look at **Browser Console** (F12) for client-side errors
3. Check **Backend Logs** for server errors
4. Review **Playwright Report** for test failures
5. Check **Database** directly with psql for data issues

---

## 🎉 Success!

Once all tests pass and you can:
- [ ] Login successfully
- [ ] Navigate between pages
- [ ] See real data from the API
- [ ] Run E2E tests without errors

You have successfully verified the complete AutoIntern implementation! 🚀

---

**Last Updated:** February 12, 2026  
**Status:** ✅ Complete with full E2E testing setup
