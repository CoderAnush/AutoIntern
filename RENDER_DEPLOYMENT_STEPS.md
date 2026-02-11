# 🚀 AutoIntern Deployment on Render - Step by Step

**Platform**: Render.com
**Cost**: FREE tier (or $7+/month for production)
**Setup Time**: 10-15 minutes
**Total Time**: 15-20 minutes from zero to live

---

## ✅ YOU ALREADY HAVE:

PostgreSQL Database:
```
postgresql://autointern_user:tFJMDfBDx1L3O9zJA78Gy4K1wauZ3hbN@dpg-d6695kogjchc73cd5abg-a/autointern
```

**We need to**:
1. Convert this to asyncpg format
2. Set up Redis (for caching/rate limiting)
3. Deploy on Render

---

## STEP 1: Convert Database URL (1 minute)

Your database URL:
```
postgresql://autointern_user:tFJMDfBDx1L3O9zJA78Gy4K1wauZ3hbN@dpg-d6695kogjchc73cd5abg-a/autointern
```

Change `postgresql://` to `postgresql+asyncpg://`:
```
postgresql+asyncpg://autointern_user:tFJMDfBDx1L3O9zJA78Gy4K1wauZ3hbN@dpg-d6695kogjchc73cd5abg-a/autointern
```

**Copy this** - you'll need it in Step 5

---

## STEP 2: Sign Up on Render (2 minutes)

1. Go to: https://render.com
2. Click **"Get Started"** in top right
3. Click **"Sign up with GitHub"** (easiest)
4. Authorize Render to access GitHub
5. Done!

---

## STEP 3: Create Redis Database (3 minutes)

### From Render Dashboard:

1. Click **"New +"** button (top right)
2. Select **"Redis"**
3. Configuration:
   - **Name**: `autointern-redis`
   - **Region**: Select closest to you
   - **Plan**: `Free` (or Standard for production)
4. Click **"Create Redis"**
5. Wait 1-2 minutes for it to provision

### Get Redis URL:

Once Redis is created:
1. Click on the Redis service
2. Look for **"Internal URL"** or **"Connections"** section
3. Copy the URL that looks like: `redis://default:PASSWORD@HOST:PORT`

**Save this** - you'll need it in Step 5

---

## STEP 4: Create Web Service (2 minutes)

### From Render Dashboard:

1. Click **"New +"** button
2. Select **"Web Service"**
3. Authorize GitHub and select your repo:
   - Click **"Connect account"** → Authorize
   - Search for `AutoIntern`
   - Click **"Connect"** next to it
4. Configuration:
   - **Name**: `autointern-api`
   - **Environment**: Python (should auto-detect)
   - **Region**: Same as Redis
   - **Branch**: `dev/init` (or `main` if you merged)
   - **Build command**: Leave blank (uses Dockerfile)
   - **Start command**: Leave blank (uses Dockerfile)
   - **Plan**: `Free` (or Standard for production)

5. Click **"Create Web Service"**

---

## STEP 5: Add Environment Variables (3 minutes)

Once web service is created:

1. Go to **"Environment"** tab (left sidebar)
2. Add the following variables:

### Add Variables:

**Click "Add Environment Variable"** and fill in each:

| Key | Value | Type |
|-----|-------|------|
| `DATABASE_URL` | `postgresql+asyncpg://autointern_user:tFJMDfBDx1L3O9zJA78Gy4K1wauZ3hbN@dpg-d6695kogjchc73cd5abg-a/autointern` | Secret ✓ |
| `REDIS_URL` | Your Redis URL from Step 3 | Secret ✓ |
| `SECRET_KEY` | See Step 6 below | Secret ✓ |
| `PYTHONUNBUFFERED` | `1` | Regular |
| `PYTHONDONTWRITEBYTECODE` | `1` | Regular |

### Mark as Secret:
For `DATABASE_URL`, `REDIS_URL`, and `SECRET_KEY`:
- Check the **"Secret"** checkbox (prevents showing in logs)

---

## STEP 6: Generate & Add Secret Key (2 minutes)

**Generate on your local machine**:

**Windows**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Mac/Linux**:
```bash
openssl rand -hex 32
```

**Copy the output** (64 characters), then:

1. Go back to Render dashboard
2. Add new environment variable:
   - **Key**: `SECRET_KEY`
   - **Value**: Paste your generated key
   - Check **"Secret"** checkbox
3. Click **"Save"**

---

## STEP 7: Deploy! (5-8 minutes)

Render automatically starts building when you save environment variables:

1. Go to **"Logs"** tab
2. Watch the deployment:
   ```
   Building from Dockerfile...
   Installing dependencies...
   Building image...
   Deploying...
   ```

3. Wait for:
   ```
   Your service is live at: https://autointern-api.onrender.com
   ```

✅ **When you see that - YOUR APP IS LIVE!**

---

## STEP 8: Verify Deployment (3 minutes)

### Test 1: Health Check
```bash
curl https://autointern-api.onrender.com/health
```

Expected:
```json
{
  "status": "healthy",
  "db": "ok",
  "redis": "ok"
}
```

### Test 2: API Documentation
Open in browser:
```
https://autointern-api.onrender.com/docs
```

Should show Swagger UI with all endpoints

### Test 3: Register User
```bash
curl -X POST https://autointern-api.onrender.com/users/register \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"TestPass123!\"}"
```

### Test 4: Login
```bash
curl -X POST https://autointern-api.onrender.com/users/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"TestPass123!\"}"
```

Should return `access_token` and `refresh_token`

---

## ✅ DEPLOYMENT COMPLETE!

Your API is now live at:
```
https://autointern-api.onrender.com
```

Use this URL in your frontend `.env`:
```
REACT_APP_API_URL=https://autointern-api.onrender.com
```

---

## 🔧 USEFUL COMMANDS

### View Logs:
Dashboard → Service → Logs (scroll to see deployment history)

### Redeploy:
Dashboard → Manual Deploy → "Deploy latest commit"

### Update Environment Variables:
Dashboard → Environment → Edit value → Save

### View Metrics:
Dashboard → Logs tab shows CPU, memory, requests

---

## 🆘 TROUBLESHOOTING

### Build failed:
1. Check Logs tab for error message
2. Most common: Missing environment variable
3. Add variable and Render auto-redeploys

### App won't start:
1. Check Logs for error
2. Verify DATABASE_URL format: `postgresql+asyncpg://...` (not `postgresql://`)
3. Verify REDIS_URL is correct
4. Restart: Manual Deploy → "Deploy latest commit"

### Health check fails:
1. Wait 2-3 minutes (first startup)
2. Check logs for errors
3. Verify database is accessible
4. Verify Redis is running

### Can't connect to database:
1. Verify DATABASE_URL is correct
2. Check username/password (case sensitive)
3. Check host is accessible from Render
4. Try redeploying

### Can't reach deployed API:
1. Wait 1-2 minutes for DNS propagation
2. Verify service shows "Live" status
3. Try browser incognito mode (clear cache)
4. Check correct URL: `https://autointern-api.onrender.com`

---

## 📊 QUICK REFERENCE

| Action | How |
|--------|-----|
| **View URL** | Dashboard → Service name shows URL |
| **View Logs** | Dashboard → Logs tab |
| **Edit Variables** | Dashboard → Environment tab |
| **Redeploy** | Dashboard → Manual Deploy → "Deploy latest" |
| **Restart Service** | Manual Deploy button (auto-triggers rebuild) |
| **Add Custom Domain** | Dashboard → Settings → Custom Domain |

---

## 💡 IMPORTANT NOTES

✅ **DO**:
- Keep SECRET_KEY secure (mark as Secret)
- Test after deployment (all 4 tests above)
- Check logs if something goes wrong
- Use custom domain (optional, for production)

❌ **DON'T**:
- Commit `.env` to GitHub
- Share SECRET_KEY or database password
- Use weak passwords
- Modify Dockerfile without testing locally

---

## 🎯 COST BREAKDOWN

### Free Tier:
- Web service (Free tier)
- Redis (Free tier)
- PostgreSQL (external, you have it)
- **Total: $0/month** ✅

### If You Scale Later:
- Web service (Starter): $7/month
- Redis (Standard): Starting $15/month
- PostgreSQL (if paid): Variable cost

---

## ✨ NEXT STEPS

### 1. Verify Everything Works
Run all 4 tests from Step 8 ✅

### 2. Connect Your Frontend
Update your React/Vue `.env`:
```
REACT_APP_API_URL=https://autointern-api.onrender.com
```

### 3. Setup Auto-Deploy (Optional)
Go to Dashboard → Settings → Auto-Deploy
- Select `dev/init` or `main` branch
- Auto-deploys on every push

### 4. Add Custom Domain (Optional)
If you have a domain:
- Dashboard → Settings → Custom Domain
- Update DNS at your registrar

### 5. Monitor Application
```bash
# Check periodically:
curl https://autointern-api.onrender.com/health
```

---

## 📝 FINAL CHECKLIST

Before considering deployment complete:

- [ ] Web service shows "Live" status (green)
- [ ] Redis shows "Available" status (green)
- [ ] Health endpoint returns 200 OK
- [ ] Swagger UI loads at `/docs`
- [ ] Can register a test user
- [ ] Can login and get access token
- [ ] Can access profile with token (`GET /users/me`)
- [ ] Logs show no errors
- [ ] API URL saved for frontend

---

## 📞 SUPPORT

- **Render Docs**: https://render.com/docs
- **GitHub**: https://github.com/CoderAnush/AutoIntern
- **Status**: https://status.render.com

---

## ⏱️ TOTAL TIME: 15-20 minutes

| Step | Time |
|------|------|
| Convert database URL | 1 min |
| Sign up Render | 2 min |
| Create Redis | 3 min |
| Create Web Service | 2 min |
| Add environment variables | 3 min |
| Generate secret key | 2 min |
| Deploy | 5-8 min |
| Test | 3 min |
| **TOTAL** | **~21 min** |

---

## 🎉 YOU'RE LIVE!

Your AutoIntern API is now deployed at:
```
https://autointern-api.onrender.com
```

Go share this with your team! 🚀

---

**Status**: ✅ READY TO DEPLOY
