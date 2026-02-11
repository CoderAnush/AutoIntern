# Deployment Guide: Render.com

**Platform**: Render.com
**Cost**: Free tier (with limitations) or $7/month ($5 web + $7 PostgreSQL)
**Setup Time**: 10-15 minutes
**Estimated Deployment Time**: 5-10 minutes

---

## Step 1: Sign Up (2 minutes)

1. Go to [render.com](https://render.com)
2. Click **"Get Started"**
3. Sign up with GitHub account (recommended for easy deployment)
4. Authorize Render to access your GitHub repositories

---

## Step 2: Create New Service (3 minutes)

1. From Render dashboard, click **"New +"** → **"Web Service"**
2. Connect your GitHub repository:
   - Select your GitHub organization/account
   - Search for `AutoIntern`
   - Click **"Connect"**

3. Configure Web Service:
   - **Name**: `autointern-api`
   - **Environment**: `Docker` (since we have Dockerfile)
   - **Region**: Select closest to you (e.g., `Oregon` for US)
   - **Plan**: `Free` (or `Standard` if you need guaranteed memory)
   - **Auto-deploy**: Enable (optional, auto-deploys on push to main)

4. Click **"Create Web Service"**

---

## Step 3: Add PostgreSQL Database (2 minutes)

1. From Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `autointern-postgres`
   - **Database**: `autointern`
   - **User**: `autointern`
   - **Region**: Same as Web Service
   - **Plan**: `Free` (or `Standard` for production)

3. Click **"Create Database"**
4. **Save the connection URL** - you'll need it shortly

---

## Step 4: Add Redis (2 minutes)

1. From Render dashboard, click **"New +"** → **"Redis"**
2. Configure:
   - **Name**: `autointern-redis`
   - **Region**: Same as Web Service
   - **Plan**: `Free` (or `Standard`)

3. Click **"Create Redis"**
4. **Save the Redis URL** - you'll need it shortly

---

## Step 5: Get Database Connection Strings (1 minute)

### PostgreSQL Connection String

1. Go to your PostgreSQL service dashboard
2. Look for **"External Database URL"** (inside info box)
3. Copy the full URL - should look like:
   ```
   postgresql://autointern:<PASSWORD>@<HOST>:<PORT>/autointern
   ```
4. **Change `postgresql://` to `postgresql+asyncpg://`** for async driver

   **Final format**:
   ```
   postgresql+asyncpg://autointern:<PASSWORD>@<HOST>:<PORT>/autointern
   ```

### Redis Connection String

1. Go to your Redis service dashboard
2. Look for **"Connection String"** or **"Internal URL"**
3. Copy it - should look like:
   ```
   redis://<HOST>:<PORT>
   ```

---

## Step 6: Set Environment Variables (3 minutes)

### On Web Service Dashboard:

1. Go to **autointern-api** service
2. Click **"Environment"** (left sidebar)
3. Add the following variables:

   | Key | Value | Type |
   |-----|-------|------|
   | `DATABASE_URL` | `postgresql+asyncpg://autointern:PASSWORD@HOST:PORT/autointern` | Secret |
   | `REDIS_URL` | `redis://HOST:PORT` | Secret |
   | `SECRET_KEY` | `<generate below>` | Secret |
   | `PYTHONUNBUFFERED` | `1` | Regular |
   | `PYTHONDONTWRITEBYTECODE` | `1` | Regular |

### Generate SECRET_KEY:

**On your local machine** (Windows):
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as the `SECRET_KEY` value.

### Mark as Secret:

- Check **"Secret"** checkbox for: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`
- This prevents them from appearing in logs

---

## Step 7: Configure Render.yaml (Optional)

The `render.yaml` file in the repo root will auto-configure services if you're using Render's Infrastructure as Code feature. If deploying manually via UI, skips this step.

---

## Step 8: Trigger Deployment (1 minute)

### Option A: Auto-Deploy (if enabled)
1. Push code to GitHub main branch:
   ```bash
   git push origin master
   ```
2. Render automatically detects and deploys

### Option B: Manual Deployment
1. Go to **autointern-api** service
2. Click **"Manual Deploy"** → **"Deploy latest commit"**
3. Watch the build process in the logs

---

## Step 9: Monitor Build (5-10 minutes)

1. Go to **autointern-api** dashboard
2. Click **"Logs"** tab
3. Watch for:
   - ✅ Docker build completing
   - ✅ Dependencies installing
   - ✅ Service starting on port 8000
   - ✅ Health check passing

**Expected final message**:
```
Application startup complete
```

---

## Step 10: Get Your Deployment URL (1 minute)

1. Go to **autointern-api** service
2. At the top, you'll see your **domain URL**: `https://autointern-api.onrender.com`
3. Save this URL!

---

## Verify Deployment

### Test Health Endpoint:
```bash
curl https://autointern-api.onrender.com/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T14:30:00Z",
  "db": "ok",
  "redis": "ok",
  "checks_passed": 2,
  "checks_total": 2
}
```

### Test Liveness:
```bash
curl https://autointern-api.onrender.com/health/live
```

### Access API Documentation:
```bash
https://autointern-api.onrender.com/docs
```

### Test User Registration:
```bash
curl -X POST https://autointern-api.onrender.com/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

**Expected response**:
```json
{
  "id": "uuid-here",
  "email": "test@example.com",
  "created_at": "2026-02-11T14:30:00Z"
}
```

---

## Troubleshooting

### Build Fails with Dependency Error

**Error**: `No module named 'xyz'`

**Solution**:
- Check services/api/requirements.txt for typos
- Verify all versions exist in PyPI
- Check build logs for specific error

### Database Connection Refused

**Error**: `could not connect to server: Connection refused`

**Solution**:
1. Verify `DATABASE_URL` is correct in Environment variables
2. Check PostgreSQL service is running (dashboard should show blue status)
3. Make sure URL uses `postgresql+asyncpg://` prefix (not `postgresql://`)

### Redis Connection Failed

**Error**: `connection refused` or `WRONGPASS`

**Solution**:
1. Copy full Redis connection string (including password if present)
2. Use format: `redis://:PASSWORD@HOST:PORT` (if auth required)
3. Test with: `redis-cli -u <YOUR_REDIS_URL> ping`

### Service Keeps Restarting

**Cause**: Application crash or memory limit

**Solution**:
1. Check logs for error messages
2. Upgrade to paid plan for more memory
3. Check if database migrations need to run

### "Port Already in Use"

**Solution**: Render auto-assigns ports, usually not an issue. Clear browser cache and try again.

---

## Cost Breakdown (2026)

### Recommended Setup (Production):

| Service | Plan | Cost |
|---------|------|------|
| Web Service | Standard | $7/month |
| PostgreSQL | Standard | $15/month |
| Redis | Standard | $15/month |
| **Total** | | **$37/month** |

### Budget Setup (Free/Development):

| Service | Plan | Cost |
|---------|------|------|
| Web Service | Free | Free ⚠️ |
| PostgreSQL | Free | Free ⚠️ |
| Redis | Free | Free ⚠️ |
| **Total** | | **Free** |

⚠️ **Note**: Free tier has limitations:
- Services spin down after 15 minutes of inactivity
- Limited CPU and memory
- Not suitable for production traffic

---

## Next Steps After Deployment

### 1. Update Frontend
Change API endpoint in your frontend `.env`:
```
REACT_APP_API_URL=https://autointern-api.onrender.com
```

### 2. Monitor Application
- Set up Render alerts for service health
- Periodically check logs for errors
- Monitor database disk usage

### 3. Enable Auto-Deploy (Optional)
1. Go to **autointern-api** service
2. Click **"Settings"**
3. Enable **"Auto-Deploy"** for GitHub pushes

### 4. Set Up Custom Domain (Optional)
1. Go to **autointern-api** service
2. Click **"Settings"** → **"Custom Domain"**
3. Add your domain and configure DNS

---

## Support & Documentation

- **Render Docs**: https://render.com/docs
- **Render Status**: https://status.render.com
- **Support**: Contact support@render.com

---

## ✅ Success Checklist

- [ ] GitHub repository connected to Render
- [ ] PostgreSQL database created and running
- [ ] Redis service created and running
- [ ] All environment variables set (DATABASE_URL, REDIS_URL, SECRET_KEY)
- [ ] Web service deployed successfully
- [ ] Health endpoint returns 200 OK
- [ ] API documentation accessible at `/docs`
- [ ] User registration endpoint working
- [ ] Frontend can connect to API URL

---

**Estimated Total Time**: 15-20 minutes
**Status**: Ready to deploy! 🚀
