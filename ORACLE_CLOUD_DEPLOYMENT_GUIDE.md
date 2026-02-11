# Deployment Guide: Oracle Cloud Always Free Tier

**Platform**: Oracle Cloud Always Free
**Cost**: FREE - Forever (no time limit, no hidden charges)
**Guaranteed Resources**:
- 2 ARM-based Compute Instances (1/8 OCPU, 1GB RAM each)
- 100GB block storage
- 20GB object storage
- 1TB/month data transfer
- PostgreSQL-compatible Autonomous Database (free tier)

**Setup Time**: 20-30 minutes
**Estimated Deployment Time**: 15-20 minutes

---

## What is Oracle Cloud Always Free?

Oracle Cloud's Always Free tier is **genuinely free forever** with no expiration date, unlike other platforms:

| Feature | Oracle Always Free | Render Free | Fly.io Free |
|---------|-----|--------|----------|
| Duration | Forever ✅ | Forever ✅ | Forever ✅ |
| Time Limit | None ✅ | None ✅ | None ✅ |
| Inactivity Deletion | No ✅ | Spin down | No ✅ |
| CPU/RAM | 2 OCPU, 2GB | Shared | Shared |
| Database | Autonomous DB (free) ✅ | Need paid | Need paid |
| Bandwidth | 1TB/month | Included | Included |
| Uptime SLA | 99.9% | Best effort | Best effort |

---

## Step 1: Create Oracle Cloud Account (5 minutes)

1. Go to [oracle.com/cloud/free](https://www.oracle.com/cloud/free/)
2. Click **"Start for Free"**
3. Enter your email and create account
4. Add payment method (required for identity verification, but **no charges** will be made)
5. Verify your email

**Important**: You'll get $300 free credits (valid for 30 days) + Always Free resources forever. The credits are optional; the Always Free tier never expires.

---

## Step 2: Create Compute Instance (Linux) (10 minutes)

### From Oracle Cloud Console:

1. Click **"Create a VM instance"** or go to **Compute** → **Instances**
2. Click **"Create Instance"**

### Configuration:

**Name**: `autointern-api`

**Image & Shape**:
- Image: **Ubuntu 22.04** (free)
- Shape: **Ampere (ARM)** → **Micro** (Always Free eligible)
  - CPU: 1/8 OCPU
  - RAM: 1 GB
- Check: ✅ **"Always Free"** (should show eligible)

**Network**:
- VCN: Create new or select existing
- Subnet: Create new (default is fine)
- Public IP: ✅ **"Assign a public IPv4 address"** (needed for access)

**SSH Key**:
- Select **"Generate SSH key pair"**
- Download the private key file - SAVE IT SECURELY
- This is how you'll log into the server

**Root Volume**:
- Size: 100 GB (Always Free allows this)

3. Click **"Create"** and wait 1-2 minutes for instance to launch

---

## Step 3: Create PostgreSQL Database (5 minutes)

### From Oracle Cloud Console:

1. Go to **Database** → **Autonomous Database**
2. Click **"Create Autonomous Database"**

### Configuration:

**Basic Info**:
- **Workload Type**: **Database** (not Data Warehouse)
- **Deployment Type**: **Shared Infrastructure** (Always Free)

**Database Configuration**:
- **Display Name**: `autointern-db`
- **Database Name**: `autointerndb` (same will be used)
- **Admin Password**: Create a strong password (save it!)

**Network Access**:
- **Access Type**: **Secure access from everywhere** (more secure)
- Or: **Secure access from allowed IPs only** (and add your IP)

**License**:
- License Type: **License Included** (free)

3. Click **"Create Autonomous Database"**
4. Wait 3-5 minutes for provisioning

**Once created**:
- Click on the database
- Go to **Database Connection** → **Show Database Actions**
- Note the **JDBC Connection String** - you'll need this

---

## Step 4: Generate Database Connection String (2 minutes)

From Autonomous Database page:

1. Click **"Database Connection"**
2. You'll see connection strings in different formats
3. For your app, use **JDBC URL** but convert it:

**From JDBC format**:
```
jdbc:oracle:thin:@autointerndb_medium?TNS_ADMIN=/path/to/wallet
```

**Convert to Python SQLAlchemy format**:
```
oracle+oracledb://autointern:PASSWORD@autointerndb_medium
```

⚠️ **Important**:
- Username: `admin`
- Database will be: `AUTOINTERNDB`
- Host/port are provided in the connection string

**Note**: We'll need to create a custom username later (not using admin for production)

---

## Step 5: Connect to Compute Instance (3 minutes)

From your local machine:

```bash
# Linux/Mac:
chmod 600 /path/to/private-key.key
ssh -i /path/to/private-key.key ubuntu@YOUR_INSTANCE_PUBLIC_IP

# Windows (PowerShell or Git Bash):
ssh -i C:\path\to\private-key.key ubuntu@YOUR_INSTANCE_PUBLIC_IP
```

**If SSH blocked by firewall**:
- In Oracle Console: Go to Instance → **Link to VCN**
- Edit **Security List** → **Ingress Rules**
- Add rule: Protocol: TCP, Source CIDR: 0.0.0.0/0, Port: 22

---

## Step 6: Install Docker & Dependencies (5 minutes)

Once connected via SSH to the instance:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Log out and back in
exit
```

Reconnect:
```bash
ssh -i /path/to/private-key.key ubuntu@YOUR_INSTANCE_PUBLIC_IP
```

Verify Docker:
```bash
docker --version  # Should show Docker version
docker run hello-world  # Should work
```

---

## Step 7: Clone Repository & Deploy (5 minutes)

```bash
# Clone your repo
git clone https://github.com/CoderAnush/AutoIntern.git
cd AutoIntern

# Create .env file with production variables
cat > AutoIntern/services/api/.env << 'EOF'
DATABASE_URL=oracle+oracledb://admin:YOUR_PASSWORD@YOUR_DB_HOST:1521/AUTOINTERNDB
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=YOUR_SECRET_KEY_HERE
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
CORS_ORIGINS=["*"]
EOF
```

**Replace**:
- `YOUR_PASSWORD`: Your Autonomous DB admin password
- `YOUR_DB_HOST`: Host from your database connection string
- `YOUR_SECRET_KEY_HERE`: Generate with:
  ```bash
  python3 -c "import secrets; print(secrets.token_hex(32))"
  ```

---

## Step 8: Optional - Add Redis (for caching/rate limiting)

If you want Redis running locally on the same instance:

```bash
# Install Redis
sudo apt install redis-server -y

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify
redis-cli ping  # Should return "PONG"
```

Then in `.env`, use:
```
REDIS_URL=redis://localhost:6379/0
```

---

## Step 9: Build & Run Application (3 minutes)

```bash
# Navigate to the API directory
cd AutoIntern

# Build Docker image (this will take 5-10 minutes)
docker build -t autointern:latest -f Dockerfile .

# Run container (detached)
docker run -d \
  --name autointern-api \
  -p 8000:8000 \
  --env-file AutoIntern/services/api/.env \
  autointern:latest

# Check logs
docker logs -f autointern-api
```

**Wait for**:
```
Application startup complete
Uvicorn running on http://0.0.0.0:8000
```

---

## Step 10: Open Firewall & Test (2 minutes)

### Open Port 8000:

1. Go back to Oracle Console
2. Navigate to **Compute** → **Instances** → Your instance
3. Click on **Primary VNIC** → **Security List**
4. Click **Add Ingress Rule**:
   - **Protocol**: TCP
   - **Source CIDR**: 0.0.0.0/0 (allow from anywhere)
   - **Destination Port Range**: 8000
   - Click **Add**

### Test API:

From your local machine:
```bash
curl http://YOUR_INSTANCE_PUBLIC_IP:8000/health

# Expected response:
# {"status": "healthy", "db": "ok", "redis": "ok"}
```

### Access API Documentation:
```
http://YOUR_INSTANCE_PUBLIC_IP:8000/docs
```

---

## Step 11: Setup Auto-Restart on Reboot (2 minutes)

Create a systemd service file so the API restarts if server reboots:

```bash
# Create service file
sudo vi /etc/systemd/system/autointern-api.service
```

Add this content:
```ini
[Unit]
Description=AutoIntern API
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/AutoIntern
ExecStart=/usr/bin/docker start -a autointern-api
ExecStop=/usr/bin/docker stop autointern-api
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable autointern-api
```

---

## Estimated Costs

### Your Setup:
- **Compute Instance**: $0 (Always Free)
- **Autonomous Database**: $0 (Always Free)
- **Block Storage**: $0 (100GB included)
- **Data Transfer**: $0 (1TB/month included)
- **Total**: **$0 - Forever** ✅

### When/If You Scale:
- Additional compute: ~$0.03/OCPU/hour
- Additional database: ~$1.25/OCPU/hour
- But you can always stay on Always Free resources

---

## Monitoring & Maintenance

### Check if Container is Running:
```bash
docker ps  # Should show autointern-api

# If not running:
docker start autointern-api
```

### View Logs:
```bash
docker logs autointern-api
docker logs -f autointern-api  # Follow logs in real-time
```

### Check Database Connection:
```bash
curl http://YOUR_PUBLIC_IP:8000/health/ready
```

### Stop/Restart Application:
```bash
docker stop autointern-api
docker start autointern-api
docker restart autointern-api
```

---

## Troubleshooting

### Cannot Connect to Server

**Error**: Connection timeout

**Solution**:
- Check Security List has port 8000 open
- Verify instance is running: `docker ps`
- Check IP is correct: `curl http://localhost:8000/health`

### Database Connection Error

**Error**: `oracle+oracledb connection failed`

**Solution**:
- Verify CONNECTION string in `.env`
- Make sure password is correct
- Test from instance: `sqlplus admin/PASSWORD@YOUR_DB_HOST:1521/AUTOINTERNDB`

### Out of Memory or Crash

**Solution**:
- Instance has 1GB RAM; if app needs more, upgrade to a paid compute instance

### Port Already in Use

**Solution**:
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill it (if needed)
sudo kill -9 PID
```

---

## Advanced: Use Domain Name (Optional)

If you want a custom domain:

1. Purchase domain from **GoDaddy**, **Namecheap**, etc.
2. Point DNS A record to your instance's **Public IP**
3. Set up **Let's Encrypt SSL** with Certbot:

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot certonly --standalone -d yourdomain.com
```

Then update your application to use HTTPS.

---

## ✅ Success Checklist

- [ ] Oracle Cloud account created
- [ ] Compute instance running (Ubuntu)
- [ ] Autonomous Database provisioned
- [ ] SSH connection working
- [ ] Docker installed
- [ ] Repository cloned
- [ ] `.env` file created with correct credentials
- [ ] Docker image built
- [ ] Container running and accessible on port 8000
- [ ] Health endpoint returns 200 OK
- [ ] API documentation accessible
- [ ] User registration endpoint working
- [ ] Auto-restart service enabled

---

## Important Notes

⚠️ **Security Best Practices**:
1. Never commit `.env` file to GitHub
2. Keep private key (`*.key`) secure
3. Use strong passwords for database
4. Regularly update system: `sudo apt update && sudo apt upgrade`
5. Monitor database usage to stay within Always Free limits

✅ **Cost Guarantee**:
- Oracle Cloud Always Free tier has **no hidden charges**
- No automatic upgrades to paid tiers
- You control exactly what resources you use
- Can run indefinitely at zero cost

---

## Support & Documentation

- **Oracle Cloud Dashboard**: https://cloud.oracle.com
- **Oracle Docs**: https://docs.oracle.com/en-us/iaas/Content/home.htm
- **Autonomous DB Guide**: https://docs.oracle.com/en-us/iaas/Content/Database/Concepts/adboverview.htm

---

**Status**: Ready to deploy forever-free! 🚀🆓
