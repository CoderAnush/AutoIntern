# 🚀 AutoIntern Deployment - Step by Step

## Quick Navigation
- **Total Time**: 20-30 minutes
- **Recommended Platform**: Fly.io (easiest, free forever)
- **Difficulty**: Easy (just follow the steps)

---

## STEP 1: Sign Up for Fly.io (2 minutes)

1. Open browser and go to: https://fly.io
2. Click **"Sign up"** button in top right
3. Choose **"Continue with GitHub"** (easiest)
4. Authorize Fly.io to access GitHub
5. Create an organization name (can be anything, e.g., your username)

**Result**: You now have a Fly.io account

---

## STEP 2: Install Fly CLI (3 minutes)

### On Windows (PowerShell):

Open PowerShell as Administrator and run:
```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

Then close and reopen PowerShell.

### On Mac/Linux:
```bash
curl -L https://fly.io/install.sh | sh
```

### Verify Installation:
```bash
flyctl version
```

Should show a version number like `v0.x.x`

---

## STEP 3: Login to Fly CLI (2 minutes)

```bash
flyctl auth login
```

A browser window will open asking to authorize. Click **"Authorize"**

**Verify login**:
```bash
flyctl auth whoami
```

Should show your email/username

---

## STEP 4: Navigate to Your Project (1 minute)

**Windows Command Prompt or PowerShell**:
```bash
cd C:\Users\anush\Desktop\AutoIntern\AutoIntern
```

**Mac/Linux**:
```bash
cd ~/Desktop/AutoIntern/AutoIntern
```

Verify you're in the right directory:
```bash
ls  # or: dir (Windows)
```

Should show files like: `Dockerfile`, `services/`, `FLY_IO_DEPLOYMENT_GUIDE.md`, etc.

---

## STEP 5: Initialize Fly.io Application (2 minutes)

Run this command:
```bash
flyctl launch --name autointern-api --region ord
```

**What this does**:
- Creates a new Fly app named `autointern-api`
- Deploys to `ord` region (Chicago - change to your region if needed)
- Detects your Dockerfile automatically

### Answer the prompts:

**1. Do you want to tweak these settings before proceeding? [y/N]:**
```
N
```
(Say NO - defaults are fine)

**2. Create Postgres cluster? [y/N]:**
```
Y
```
(Say YES - creates database)

**3. Select a Postgres version:**
```
Select default (usually 14 or 15)
```

**4. Create Redis cluster? [y/N]:**
```
Y
```
(Say YES - creates cache)

**5. Deploy now? [y/N]:**
```
N
```
(Say NO - we need to add secrets first)

**Result**: Creates a `fly.toml` file (deployment config)

---

## STEP 6: Generate Secret Key (1 minute)

Run this command:

**Windows (Command Prompt or PowerShell)**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Mac/Linux**:
```bash
openssl rand -hex 32
```

**Copy the output** - it looks like:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

---

## STEP 7: Set Environment Variables (2 minutes)

Back in terminal, run these commands **one at a time**:

### Set SECRET_KEY:
Replace `YOUR_SECRET_KEY` with the key you copied in Step 6:

**Windows PowerShell**:
```powershell
flyctl secrets set SECRET_KEY="YOUR_SECRET_KEY" -a autointern-api
```

**Mac/Linux/Command Prompt**:
```bash
flyctl secrets set SECRET_KEY="YOUR_SECRET_KEY" -a autointern-api
```

### Verify it was set:
```bash
flyctl secrets list -a autointern-api
```

Should show `SECRET_KEY` in the list.

**Note**: `DATABASE_URL` and `REDIS_URL` were set automatically when we created the clusters!

---

## STEP 8: Deploy Application (8-10 minutes)

Run this command:
```bash
flyctl deploy
```

**What happens**:
1. Builds Docker image (2-3 min)
2. Pushes to Fly.io registry (1-2 min)
3. Starts application (1-2 min)
4. Health check (30 sec)

### Watch the output:

You'll see progress like:
```
Building image with Docker
 => ...
 => DOCKERFILE ... ✓

Pushing image to Fly
  registry.fly.io/autointern-api:deployment-...

Creating release
  Release ID: ...

Monitoring deployment
  Machines are being started
  [f0a...0c6] Starting machine f0a...0c6 from image registry.fly.io/autointern-api:...
  Health checks: passed

Deployment successful
Visit your newly deployed app at https://autointern-api.fly.dev/
```

**If you see**: `Deployment successful` ✅ **YOUR APP IS LIVE!**

---

## STEP 9: Test Your Deployment (3 minutes)

### Test 1: Open API in Browser

```bash
flyctl open
```

Or manually visit:
```
https://autointern-api.fly.dev/
```

You should see Swagger UI with all your API endpoints!

### Test 2: Health Check

```bash
curl https://autointern-api.fly.dev/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T20:30:00Z",
  "db": "ok",
  "redis": "ok",
  "checks_passed": 2,
  "checks_total": 2
}
```

### Test 3: API Documentation

Open in browser:
```
https://autointern-api.fly.dev/docs
```

Should show Swagger UI with all endpoints

### Test 4: Register a User

```bash
curl -X POST https://autointern-api.fly.dev/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

Expected response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "test@example.com",
  "created_at": "2026-02-11T20:30:00Z"
}
```

### Test 5: Login

```bash
curl -X POST https://autointern-api.fly.dev/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

✅ **All tests passing? Your API is LIVE and working!**

---

## STEP 10: Get Your API Endpoint (1 minute)

Your API is now live at:
```
https://autointern-api.fly.dev
```

**Save this URL!** You'll need it when connecting your frontend.

### Commands to remember:

```bash
# View logs
flyctl logs -a autointern-api

# Stop/restart app
flyctl restart -a autointern-api

# View metrics
flyctl metrics -a autointern-api

# Check status
flyctl status -a autointern-api

# View secrets
flyctl secrets list -a autointern-api

# Access database
flyctl postgres connect -a autointern-api-db

# Access Redis
flyctl redis connect -a autointern-api-redis
```

---

## ✅ DEPLOYMENT COMPLETE!

Congratulations! Your AutoIntern API is now deployed and accessible at:

```
🎉 https://autointern-api.fly.dev 🎉
```

### What you can do now:

1. **Share your API** with team members
2. **Connect your frontend** (React/Vue/etc) to this URL
3. **Monitor logs** with `flyctl logs -a autointern-api --follow`
4. **Scale if needed** with `flyctl scale vm`
5. **Add custom domain** (optional) with `flyctl certs add yourdomain.com`

---

## 🔧 TROUBLESHOOTING

### Problem: "App won't start"

**Solution**:
```bash
flyctl logs -a autointern-api
```

Check the error message. Common issues:
- Missing environment variable → Add with `flyctl secrets set`
- Database not ready → Wait 30 seconds and retry
- Port issue → Fly auto-assigns ports, should be fine

### Problem: "Database connection refused"

**Solution**:
```bash
# Verify DATABASE_URL exists
flyctl secrets list -a autointern-api

# If missing, Fly should have created it. Restart:
flyctl restart -a autointern-api
```

### Problem: "Health check failed"

**Solution**:
```bash
# Wait 60 seconds (health check grace period)
# Check logs
flyctl logs -a autointern-api --follow

# Restart
flyctl restart -a autointern-api
```

### Problem: "Deploy failed during build"

**Solution**:
```bash
# Read error message in logs
flyctl logs -a autointern-api

# Check requirements.txt is valid
cat services/api/requirements.txt

# Try again
flyctl deploy
```

### Problem: Can't access https://autointern-api.fly.dev

**Solution**:
```bash
# Verify app is running
flyctl status -a autointern-api

# Get correct URL
flyctl open  # Automatically opens current URL

# Wait 2-3 minutes for DNS to propagate
```

---

## 📊 NEXT STEPS

### 1. Connect Frontend (if you have one)

Update your React/Vue `.env` file:
```
REACT_APP_API_URL=https://autointern-api.fly.dev
```

Then use in your frontend:
```javascript
const API_URL = process.env.REACT_APP_API_URL;

// Register
fetch(`${API_URL}/users/register`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})

// Login
fetch(`${API_URL}/users/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})
```

### 2. Monitor Application

```bash
# Watch logs in real-time
flyctl logs -a autointern-api --follow

# Check every minute
watch "flyctl status -a autointern-api"
```

### 3. Setup Auto-Deploy from GitHub (Optional)

So every time you push to GitHub, it auto-deploys:

```bash
flyctl dashboard
# Go to app → Settings → GitHub Integration
# Connect GitHub account
# Select AutoIntern repo
# Enable auto-deploy on push
```

### 4. Add Custom Domain (Optional)

If you own a domain:
```bash
# Point domain to Fly
flyctl certs add yourdomain.com -a autointern-api

# Then update DNS at your registrar (GoDaddy, etc.)
# Add CNAME record pointing to Fly's address
```

### 5. Scale if Traffic Grows

```bash
# Upgrade CPU/Memory
flyctl scale vm shared-cpu-2x -a autointern-api

# Add more instances
flyctl scale count 3 -a autointern-api

# Upgrade database
flyctl postgres scale-up -a autointern-api-db
```

---

## 💡 IMPORTANT REMINDERS

✅ **DO**:
- Keep your SECRET_KEY secure
- Monitor logs regularly
- Test endpoints after changes
- Use custom domain in production
- Plan scaling before traffic surge

❌ **DON'T**:
- Commit `.env` to GitHub
- Share your SECRET_KEY
- Use weak passwords
- Ignore errors in logs
- Forget to update API_URL in frontend

---

## 📞 SUPPORT

If something goes wrong:

1. **Check Logs First**:
   ```bash
   flyctl logs -a autointern-api --follow
   ```

2. **Read Error Message**: Most errors are self-explanatory

3. **Restart App**:
   ```bash
   flyctl restart -a autointern-api
   ```

4. **Check Status**:
   ```bash
   flyctl status -a autointern-api
   ```

5. **Refer to Guides**:
   - Full guide: `FLY_IO_DEPLOYMENT_GUIDE.md`
   - All options: `DEPLOYMENT.md`
   - Pre-checks: `PRODUCTION_READINESS_CHECKLIST.md`

6. **Contact Support**: https://fly.io/docs

---

## 🎯 SUMMARY

| Step | Command | Time |
|------|---------|------|
| 1. Sign up | flyctl.io | 2 min |
| 2. Install CLI | Install flyctl | 3 min |
| 3. Login | `flyctl auth login` | 2 min |
| 4. Navigate | `cd AutoIntern` | 1 min |
| 5. Initialize | `flyctl launch` | 2 min |
| 6. Generate secret | `python -c "..."` | 1 min |
| 7. Set secrets | `flyctl secrets set` | 2 min |
| 8. Deploy | `flyctl deploy` | 10 min |
| 9. Test | `curl https://...` | 3 min |
| 10. Save URL | Copy endpoint | 1 min |
| | **TOTAL** | **27 min** |

---

**Your app is live in ~30 minutes! 🚀**

Good luck! Feel free to ask if you get stuck on any step.
