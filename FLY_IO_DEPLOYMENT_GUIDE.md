# Deployment Guide: Fly.io

**Platform**: Fly.io
**Cost**: FREE - Forever (no time limit, no hidden charges)
**Guaranteed Resources** (Free Tier):
- 3 Free Compute: ~1-2 CPU cores shared
- 3 Free Databases (PostgreSQL/Redis/MySQL)
- 160GB outbound data transfer per month
- 40GB inbound data transfer per month
- Unlimited inbound connections

**Setup Time**: 15-20 minutes
**Estimated Deployment Time**: 5-10 minutes

---

## What is Fly.io?

Fly.io is a **modern platform** that runs your code on edge infrastructure close to users:

| Feature | Fly.io Free | Oracle Always Free | Render Free |
|---------|---------|--------|---------|
| Duration | Forever ✅ | Forever ✅ | Forever ✅ |
| No Deletion | Yes ✅ | Yes ✅ | Yes ✅ |
| Database Included | Yes ✅ | Yes ✅ | No ❌ |
| 3 Free Compute Apps | Yes ✅ | No | No |
| Global Distribution | Yes ✅ | No | No |
| Auto-scaling | Yes ✅ | No | No |
| Easy GitHub Deploy | Yes ✅ | No | Yes ✅ |
| Setup Complexity | Simple ✅ | Medium | Simple ✅ |

---

## Key Advantages

✅ **No Time Limits** - Free tier never expires
✅ **No Credit Card Required** - (Though recommended for protection)
✅ **Multiple Free Apps** - Deploy up to 3 apps free
✅ **Databases Included** - PostgreSQL, Redis, MySQL all free
✅ **Auto-deploy from GitHub** - Push and deploy instantly
✅ **Global** - Your app runs close to users worldwide
✅ **Simple CLI** - Easy commands, no web UI needed
✅ **Production-Ready** - Used by real companies

---

## Step 1: Sign Up (2 minutes)

### Option A: GitHub Sign-In (Recommended)

1. Go to [fly.io](https://fly.io)
2. Click **"Sign up"**
3. Choose **"Continue with GitHub"**
4. Authorize Fly.io to access GitHub
5. Create your organization name (e.g., your username)

### Option B: Email Sign-Up

1. Click **"Sign up"** at fly.io
2. Enter email and password
3. Verify email
4. Create organization name

---

## Step 2: Install Fly CLI (3 minutes)

### On Windows (PowerShell):
```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### On Mac/Linux:
```bash
curl -L https://fly.io/install.sh | sh
```

### Verify Installation:
```bash
flyctl version
```

---

## Step 3: Login to Fly (1 minute)

```bash
flyctl auth login
```

This opens a browser to authenticate. Once done:

```bash
flyctl auth whoami  # Verify you're logged in
```

---

## Step 4: Deploy Your App (5 minutes)

### Navigate to Repository:
```bash
cd C:\Users\anush\Desktop\AutoIntern\AutoIntern
```

### Initialize Fly App:
```bash
flyctl launch --name autointern-api --region ord
```

**Prompts**:
- **App name**: `autointern-api`
- **Region**: Choose closest to you (e.g., `ord` = Chicago, `sfo` = San Francisco)
- **Postgres database**: Select **"Yes"** (adds free PostgreSQL)
- **Redis database**: Select **"Yes"** (adds free Redis)
- **Deploy now**: Select **"No"** (we'll configure first)

This creates a `fly.toml` file (deployment config).

---

## Step 5: Update fly.toml Configuration

The file was created, but let me show you what it should look like:

```toml
app = "autointern-api"
primary_region = "ord"

[build]
  dockerfile = "Dockerfile"
  args = { BUILDKIT_INLINE_CACHE = "1" }

[env]
  PYTHONUNBUFFERED = "true"
  PYTHONDONTWRITEBYTECODE = "true"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[services]]
  protocol = "tcp"
  internal_port = 8000
  processes = ["app"]

  [services.concurrency]
    type = "connections"
    hard_limit = 100
    soft_limit = 80

  [[services.ports]]
    port = 443
    handlers = ["https", "tls"]

  [[services.ports]]
    port = 80
    handlers = ["http"]

[checks]
  [checks.http_check]
    grace_period = "30s"
    interval = "30s"
    method = "GET"
    path = "/health"
    protocol = "http"
    timeout = "10s"
    tls_skip_verify = false
```

---

## Step 6: Set Environment Variables

Get database connection strings that Fly created:

```bash
flyctl postgres connect -a autointern-api-db
```

This shows your PostgreSQL connection string. Note it down.

### Set Secrets:

```bash
# Generate SECRET_KEY
$secretKey = (python -c "import secrets; print(secrets.token_hex(32))")

# Set environment variables
flyctl secrets set SECRET_KEY="$secretKey" -a autointern-api
flyctl secrets set PYTHONUNBUFFERED="1" -a autointern-api
flyctl secrets set PYTHONDONTWRITEBYTECODE="1" -a autointern-api

# The DATABASE_URL and REDIS_URL are automatically set by Fly!
# Verify they're set:
flyctl secrets list -a autointern-api
```

---

## Step 7: Deploy Application

```bash
flyctl deploy
```

**What happens**:
1. ✅ Docker image builds
2. ✅ Image pushed to Fly registry
3. ✅ Machine provisioned
4. ✅ Container starts
5. ✅ Health check runs
6. ✅ Domain is assigned

**Expected output**:
```
Watch your deployment at https://fly.io/apps/autointern-api/monitoring

Provisioning 1 of 1 machines with image registry.fly.io/autointern-api:deployment-...
  Machine f0a...0c6 [app] update succeeded

Health check machine f0a...0c6 curl http://localhost:8000/health

[-] Waiting for 60 seconds before checking machine health...
Health checks: passed

Visit your newly deployed app at https://autointern-api.fly.dev/
```

---

## Step 8: Verify Deployment (2 minutes)

### Get Your App URL:
```bash
flyctl open  # Opens your app automatically
# Or visit: https://autointern-api.fly.dev
```

### Test Health Endpoint:
```bash
curl https://autointern-api.fly.dev/health

# Expected response:
# {"status": "healthy", "db": "ok", "redis": "ok", ...}
```

### Access API Documentation:
```
https://autointern-api.fly.dev/docs
```

### Test Registration:
```bash
curl -X POST https://autointern-api.fly.dev/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

---

## Useful Fly CLI Commands

### View Logs:
```bash
flyctl logs -a autointern-api
flyctl logs -a autointern-api --follow  # Real-time
```

### Check Status:
```bash
flyctl status -a autointern-api
```

### Scale App (if needed):
```bash
flyctl scale count 2 -a autointern-api  # 2 instances
flyctl scale vm shared-cpu-1x -a autointern-api  # Upgrade CPU
```

### Restart App:
```bash
flyctl restart -a autointern-api
```

### View Secrets:
```bash
flyctl secrets list -a autointern-api
```

### Update Secrets:
```bash
flyctl secrets set SECRET_KEY="new-value" -a autointern-api
```

### SSH into Machine:
```bash
flyctl ssh console -a autointern-api
```

### Database Options:
```bash
# Connect to PostgreSQL
flyctl postgres connect -a autointern-api-db

# Connect to Redis
flyctl redis connect -a autointern-api-redis
```

---

## Monitoring & Maintenance

### View Real-time Metrics:
```bash
flyctl metrics -a autointern-api
```

### Set Up Monitoring:
1. Go to [fly.io/apps/autointern-api](https://fly.io/apps/autointern-api)
2. Click **"Monitoring"** to see CPU, Memory, Network
3. Click **"Alerting"** to set up notifications

### Database Backups:
Fly automatically handles backups for free tier. Access your database:

```bash
# PostgreSQL
flyctl postgres connect -a autointern-api-db

# Then run SQL commands like:
# \dt  -- list tables
# SELECT * FROM users;
```

---

## Troubleshooting

### App Won't Start

**Error**: `Health checks: failed`

**Solution**:
```bash
# Check logs
flyctl logs -a autointern-api

# If build failed:
flyctl deploy --build-only  # Debug just the build

# Check Dockerfile
cat Dockerfile
```

### Database Connection Error

**Error**: `could not connect to database`

**Solution**:
```bash
# Check if DB is running
flyctl status -a autointern-api-db

# Verify connection string
flyctl secrets list -a autointern-api
# DATABASE_URL should be set automatically
```

### Out of Memory

**Error**: `OOMKilled` or memory exceeded

**Solution**:
```bash
# Upgrade to paid tier (if needed)
flyctl scale vm shared-cpu-2x -a autointern-api

# Or optimize app usage
```

### Too Many Connections

**Error**: `maximum number of connections`

**Solution**:
```bash
# Reduce concurrent connections in fly.toml
# Or upgrade PostgreSQL plan
```

### HTTPS Certificate Error

**Solution**: Fly auto-generates HTTPS certificates
- Wait 60 seconds for certificate to generate
- Clear browser cache
- Try again in incognito mode

---

## Cost Breakdown

### Free Tier (Forever):
```
3 Shared-CPU 1x 256MB machines  = $0
PostgreSQL database (free)      = $0
Redis database (free)           = $0
Transfer (160GB out/40GB in)    = $0
─────────────────────────────────
TOTAL                           = $0/month FOREVER ✅
```

### When You Scale (Optional):
```
Shared-CPU 1x, 256MB            = $1.97/machine/mo
Shared-CPU 2x, 1GB              = $3.94/machine/mo
Dedicated CPU, 2GB              = $9.50/machine/mo
PostgreSQL (paid)               = $15/mo
Redis (paid)                    = Starting $30/mo
```

---

## Custom Domain (Optional)

1. Purchase domain from GoDaddy, Namecheap, etc. (~$10/year)
2. Point to Fly:

```bash
flyctl certs add yourdomain.com -a autointern-api
```

3. Update DNS records based on Fly's instructions
4. Fly handles HTTPS automatically

---

## Auto-Deploy from GitHub (Optional)

1. Connect GitHub to Fly:
```bash
flyctl dashboard  # Opens dashboard
```

2. In dashboard: **Apps** → **autointern-api** → **Settings** → **GitHub Integration**
3. Connect your GitHub account
4. Enable auto-deploy on push

Now every time you push to main:
- GitHub triggers Fly
- App auto-deploys
- Old version rolled back if new version fails

---

## ✅ Success Checklist

- [ ] Fly CLI installed and authenticated
- [ ] Repository initialized with `flyctl launch`
- [ ] PostgreSQL database created
- [ ] Redis cache created
- [ ] Environment variables set
- [ ] App deployed successfully
- [ ] Health endpoint returns 200 OK
- [ ] API documentation accessible
- [ ] User registration working
- [ ] Database connected and working
- [ ] Logs are clean (no errors)
- [ ] App URL saved for frontend use

---

## Important Notes

⚠️ **Free Tier Limits**:
- 3 free machines total (can be 1 app with 3 instances, or 3 different apps)
- Each machine: ~1-2 CPU, 256MB-1GB RAM
- Transfer: 160GB/month outbound
- If you exceed, charges apply (~$0.02-0.10 per unit)

✅ **Always Free Resources**:
- PostgreSQL database (always free tier available)
- Redis database (always free tier available)
- Basic monitoring and alerting
- HTTPS certificates
- Global distribution

---

## Support & Resources

- **Fly Docs**: https://fly.io/docs/
- **Dashboard**: https://fly.io/dashboard
- **Status Page**: https://status.fly.io
- **Community Discord**: https://fly.io/discord
- **GitHub Issues**: https://github.com/superfly/fly

---

## Next Steps

After deployment:

1. **Frontend Setup**: Update API endpoint in React/Vue app
2. **Custom Domain**: Add your domain (optional)
3. **GitHub Integration**: Enable auto-deploy (optional)
4. **Monitoring**: Set up alerts in dashboard
5. **Scale as Needed**: Upgrade if traffic grows

---

**Status**: Ready to deploy to Fly.io! 🚀
