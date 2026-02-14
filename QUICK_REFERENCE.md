# 🎯 AutoIntern E2E Testing - Quick Reference

## ✅ All Credentials & Quick Links

### Test User Accounts

| Account | Email | Password | Usage |
|---------|-------|----------|-------|
| **Primary** | `test@example.com` | `TestPass123!` | Main E2E testing |
| **Demo** | `demo@autointern.com` | `DemoPass123!` | Demo presentation |
| **Admin** | `admin@autointern.com` | `AdminPass123!` | Admin testing |
| **Sample 1** | `john.doe@example.com` | `JohnDoe123!` | Profile testing |
| **Sample 2** | `jane.smith@example.com` | `JaneSmith123!` | Profile testing |

---

## 🚀 Quickest Startup (One Command)

### Option 1: PowerShell Script (Windows - Easiest)

```powershell
# From project root
cd AutoIntern
.\start-all-services.ps1
```

This will:
- Start PostgreSQL & Redis (Docker)
- Seed test users
- Start backend API (new window)
- Start frontend (current window)

---

### Option 2: Docker Compose (Cross-Platform)

```bash
cd AutoIntern
docker-compose up -d
cd services/api && python seed_test_users.py
```

Then in separate terminals:
```bash
# Terminal 1: Backend
cd services/api && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd services/web/apps/dashboard && npm run dev
```

---

## 📍 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main dashboard |
| **Backend API** | http://localhost:8000 | REST API |
| **API Docs** | http://localhost:8000/docs | Swagger docs |
| **PostgreSQL** | localhost:5432 | Database |
| **Redis** | localhost:6379 | Cache/Rate limiting |

---

## ✨ Test Login Flow (Browser Manual Test)

1. **Open** → http://localhost:3000
2. **See** → Landing page with "Land Your Dream Internship with AI"
3. **Click** → "Sign In" button
4. **Enter**:
   - Email: `test@example.com`
   - Password: `TestPass123!`
5. **Click** → "Sign In"
6. **See** → "Welcome back!" toast
7. **Verify** → Redirected to dashboard
8. **Check** → Navigation menu appears
9. **Try** → Click on "Jobs", "Analyzer", "Applications"

---

## 🧪 Run Automated E2E Tests

```powershell
cd services/web/apps/dashboard

# Install Playwright browsers (first time only)
npx playwright install

# Run all tests
npx playwright test

# View interactive test runner
npx playwright test --ui

# Watch mode (re-runs on file change)
npx playwright test --watch

# View HTML report
npx playwright show-report
```

### What Tests Cover

✅ Landing page rendering  
✅ Login form validation  
✅ Valid credential login  
✅ Invalid credential rejection  
✅ Dashboard redirect  
✅ Navigation menu  
✅ Protected routes  
✅ Logout flow  
✅ Registration flow  
✅ Password visibility toggle  
✅ Error handling  

---

## 🔍 API Testing (curl)

### Test Credentials

```bash
# Export for easy use
$email = "test@example.com"
$password = "TestPass123!"
```

### Login

```powershell
$response = curl -X POST http://localhost:8000/api/auth/login `
  -H "Content-Type: application/json" `
  -d "{`"email`":`"test@example.com`",`"password`":`"TestPass123!`"}"

# Save token for next request
$token = $response.access_token
```

### Get User Profile

```powershell
curl -X GET http://localhost:8000/api/auth/me `
  -H "Authorization: Bearer $token"
```

### Change Password

```powershell
curl -X POST http://localhost:8000/api/auth/change-password `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{
    "old_password": "TestPass123!",
    "new_password": "NewPass456!"
  }'
```

---

## 📋 Database Verification

### Check Test Users Created

```powershell
# Connect to database
psql -U autointern -d autointern -h localhost

# List users
SELECT id, email, is_active, created_at FROM users;

# Exit
\q
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 5432 in use** | `docker kill autointern-postgres && docker rm autointern-postgres` |
| **Port 3000 in use** | `taskkill /FI "WINDOWTITLE eq *npm*" /T /F` |
| **Port 8000 in use** | Change API port in startup script or `.env` |
| **Database not ready** | Wait 5-10 seconds, retry |
| **CORS errors** | Verify `.env` has correct CORS_ORIGINS |
| **Redis not found** | Check Docker is running, restart it |
| **Login fails "500"** | Check backend logs: `http://localhost:8000/health` |
| **Tests timeout** | Increase timeout in `playwright.config.ts` |

---

## 📊 Full Setup Checklist

- [ ] Clone repo
- [ ] PostgreSQL running
- [ ] Redis running
- [ ] Test users seeded
- [ ] Backend API running
- [ ] Frontend running
- [ ] Can access http://localhost:3000
- [ ] Can login with test credentials
- [ ] E2E tests pass
- [ ] All 5 navigation pages accessible

---

## 🎯 Password Requirements

All passwords must have:
- ✓ Minimum 8 characters
- ✓ At least 1 UPPERCASE letter
- ✓ At least 1 lowercase letter
- ✓ At least 1 number (0-9)
- ✓ At least 1 special character (!@#$%^&*)

**Example Valid Passwords:**
- `TestPass123!`
- `DemoPass123!`
- `AdminPass123!`
- `JohnDoe123!`
- `JaneSmith123!`

---

## 📚 File Locations

| File | Location |
|------|----------|
| Test Seeder | `services/api/seed_test_users.py` |
| E2E Tests | `services/web/apps/dashboard/e2e/auth.spec.ts` |
| Playwright Config | `services/web/apps/dashboard/playwright.config.ts` |
| Backend API | `services/api/app/main.py` |
| Frontend App | `services/web/apps/dashboard/app/` |
| Login Page | `services/web/apps/dashboard/app/(auth)/login/page.tsx` |
| API Client | `services/web/apps/dashboard/lib/api.ts` |
| Auth Store | `services/web/apps/dashboard/stores/auth-store.ts` |
| Full Guide | `E2E_TESTING_COMPLETE_GUIDE.md` |

---

## 🔐 Security Notes

- ✅ Passwords hashed with Argon2
- ✅ JWT tokens (access: 30 min, refresh: 7 days)
- ✅ Rate limiting (5 login attempts/5 min)
- ✅ Account lockout (after 5 failed attempts, 15 min lock)
- ✅ CORS protection
- ✅ SQL injection prevention
- ✅ HTTPS ready for production

---

## 🎓 What Was Implemented

### Backend Features
- ✅ User registration with password validation
- ✅ Login with JWT tokens
- ✅ Rate limiting (Redis)
- ✅ Account lockout protection
- ✅ Password change endpoint
- ✅ Token refresh endpoint
- ✅ User profile endpoint
- ✅ Logout endpoint
- ✅ Email notifications queue (Phase 7)

### Frontend Features
- ✅ Landing page (hero, features, pricing)
- ✅ Login form (email, password, show/hide toggle)
- ✅ Register form (email, password, validation)
- ✅ Protected routes (auth guard)
- ✅ Dashboard (real API integration)
- ✅ Jobs page (search, filter, apply)
- ✅ Analyzer page (resume upload, ATS scoring)
- ✅ Applications page (Kanban board)
- ✅ Settings page (profile, password, notifications)
- ✅ Assistant page (career chat)
- ✅ Navigation menu
- ✅ User profile/settings menu
- ✅ Toast notifications

### E2E Testing
- ✅ Comprehensive test suite (15+ tests)
- ✅ Playwright configuration
- ✅ Chrome, Firefox, Safari support
- ✅ Mobile testing (iOS, Android viewports)
- ✅ Screenshots on failure
- ✅ Video recording on failure
- ✅ HTML report generation
- ✅ CI/CD ready

---

## 📞 Need Help?

1. **Read** → `E2E_TESTING_COMPLETE_GUIDE.md` (detailed)
2. **Check** → Backend logs: `http://localhost:8000/health`
3. **Open** → Browser DevTools (F12) → Console & Network tabs
4. **Review** → Test results: `npx playwright show-report`
5. **Connect** → Database: `psql -U autointern -d autointern -h localhost`

---

## 🎉 Success Indicators

When everything is working:

```
✓ http://localhost:3000 loads instantly
✓ Login page renders with form
✓ Can login with test@example.com / TestPass123!
✓ See "Welcome back!" success toast
✓ Redirected to dashboard
✓ Navigation menu shows all 5+ pages
✓ E2E tests show 15+ tests passed
✓ No console errors
✓ API returns valid JSON responses
```

---

**Last Updated:** February 12, 2026  
**Status:** ✅ Ready for E2E testing  
**Test Coverage:** 15+ automated tests
