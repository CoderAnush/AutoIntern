# 🚀 AutoIntern Deployment Guide

**Status**: Production Ready
**Date**: February 11, 2026
**Version**: 1.0

---

## Quick Start (5 minutes)

### Option 1: Railway.app (EASIEST - Recommended)

```bash
# 1. Install Railway CLI
curl -L railway.app/install.sh | bash

# 2. Login to Railway
railway login

# 3. Create a new project
railway init

# 4. Link to your GitHub repo (or use current directory)
railway link

# 5. Add environment variables
railway variable add DATABASE_URL "postgresql://..."
railway variable add SECRET_KEY "your-secret-key"
railway variable add REDIS_URL "redis://..."

# 6. Deploy
railway up

# 7. View logs
railway logs

# 8. Get deployment URL
railway status
```

**Estimated time**: 5-10 minutes
**Cost**: Free tier or $5/month

---

### Option 2: Heroku (Also Easy)

```bash
# 1. Install Heroku CLI
npm install -g heroku

# 2. Login
heroku login

# 3. Create app
heroku create autointern-api

# 4. Add PostgreSQL add-on
heroku addons:create heroku-postgresql:hobby-dev

# 5. Add Redis add-on
heroku addons:create heroku-redis:premium-0

# 6. Set environment variables
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set REDIS_URL="redis://..."

# 7. Deploy
git push heroku main

# 8. View logs
heroku logs --tail
```

**Estimated time**: 10-15 minutes
**Cost**: $50-100/month for production

---

### Option 3: Docker + Your Server (AWS/DigitalOcean)

```bash
# 1. Build Docker image
docker build -f services/api/Dockerfile -t autointern-api:latest .

# 2. Run locally to test
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="your-secret-key" \
  -e REDIS_URL="redis://..." \
  autointern-api:latest

# 3. Push to Docker Registry (DockerHub/ECR)
docker tag autointern-api:latest your-registry/autointern-api:latest
docker push your-registry/autointern-api:latest

# 4. Deploy to your server
# (Instructions depend on your hosting provider)
```

---

## Environment Variables Required

### Essential (Required for all deployments)

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/autointern

# JWT Secret (generate with: openssl rand -hex 32)
SECRET_KEY=your-64-character-random-secret-key-here

# Redis
REDIS_URL=redis://default:password@host:6379/0
```

### Optional (Email notifications)

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=noreply@yourdomain.com
SENDER_PASSWORD=your-app-specific-password
```

### Optional (Storage)

```bash
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=resumes
```

---

## Pre-Deployment Checklist

- [ ] All tests passing: `pytest tests/ -v`
- [ ] Database URL ready (PostgreSQL)
- [ ] Redis URL ready
- [ ] SECRET_KEY generated (32+ random chars)
- [ ] Email credentials (if using email)
- [ ] Domain name (optional but recommended)
- [ ] SSL certificate (auto-handled by Railway/Heroku)

---

## Post-Deployment Verification

### 1. Health Check
```bash
curl https://your-domain.com/health
# Expected response:
# {"status": "healthy", "timestamp": "2026-02-11T...", "db": "ok", "redis": "ok"}
```

### 2. Liveness Probe
```bash
curl https://your-domain.com/health/live
# Expected response: {"status": "live"}
```

### 3. Readiness Probe
```bash
curl https://your-domain.com/health/ready
# Expected response: {"status": "ready", "db": "ok", "redis": "ok"}
```

### 4. API Documentation
```bash
curl https://your-domain.com/docs
# Opens interactive Swagger UI
```

### 5. Test Authentication
```bash
# Register
curl -X POST https://your-domain.com/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'

# Login
curl -X POST https://your-domain.com/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'
```

---

## Database Migration

### On First Deployment

```bash
# SSH into your deployed instance or use Railway CLI:
railway run alembic upgrade head
```

### After Each Phase Update

```bash
railway run alembic upgrade head
```

---

## Monitoring & Logs

### Railway
```bash
railway logs --follow
```

### Heroku
```bash
heroku logs --tail
```

### Docker (Local)
```bash
docker logs -f container_id
```

---

## Scaling Notes

### For 1,000+ concurrent users:

1. **Database**: Upgrade to production-grade PostgreSQL
   - RDS on AWS
   - Managed PostgreSQL on Railway/Heroku

2. **Redis**: Upgrade to managed Redis
   - ElastiCache on AWS
   - Redis Cloud
   - Railway managed Redis

3. **Application**: Scale horizontally
   - Multiple container instances
   - Load balancer (nginx/HAProxy)
   - Auto-scaling based on CPU/memory

4. **Storage**: Upgrade if using file uploads
   - AWS S3
   - MinIO (self-hosted)

---

## Troubleshooting

### Container fails to start
```bash
# Check logs
railway logs -n 50  # Last 50 lines

# Common issues:
# 1. Missing environment variables
# 2. Database connection timeout
# 3. Redis connection timeout
```

### 502 Bad Gateway
```bash
# Application is crashing - check logs:
railway logs --follow

# Common causes:
# 1. Database unreachable
# 2. Redis unreachable
# 3. Import errors
```

### Health check failing
```bash
# Verify all services are up:
curl https://your-domain.com/health

# If failing, check:
# 1. DATABASE_URL is correct
# 2. REDIS_URL is correct
# 3. Database is running
# 4. Redis is running
```

---

## Security Checklist

- [x] SSL/TLS enforced (automatic on Railway/Heroku)
- [x] Rate limiting enabled (5 login/5min)
- [x] Account lockout enabled (5 failures → 15min lock)
- [x] OWASP security headers added
- [x] CORS configured
- [x] Password hashing (bcrypt 12 rounds)
- [x] JWT tokens (30-min access, 7-day refresh)
- [x] Request logging enabled
- [ ] Secrets not in code (use environment variables)
- [ ] Database credentials not in logs

---

## Rollback Procedure

If deployment has issues:

### Railway
```bash
# Rollback to previous deployment
railway rollback
```

### Heroku
```bash
# Rollback to previous release
heroku releases
heroku rollback v5  # Or specific version
```

### Docker
```bash
# Redeploy previous version
docker run -p 8000:8000 autointern-api:v1.0
```

---

## Next Steps After Deployment

1. **Monitor**: Watch logs for errors
2. **Test**: Run integration tests against production
3. **Document**: Update API docs
4. **Frontend**: Start building frontend UI
5. **Scaling**: Monitor performance and scale as needed

---

## Support URLs

- API Docs: `https://your-domain.com/docs`
- Health: `https://your-domain.com/health`
- Metrics: `https://your-domain.com/metrics/summary`

---

## Success Metrics

After deployment, you should see:

- ✅ All health checks passing
- ✅ API responding within 200ms
- ✅ User registration working
- ✅ Authentication working
- ✅ Resume uploads working
- ✅ Job recommendations loading
- ✅ Email notifications sending
- ✅ Security headers present
- ✅ Logs being recorded
- ✅ No errors in production logs

---

## Contact & Issues

For deployment issues:
1. Check logs: `railway logs --tail`
2. Verify environment variables: `railway variable list`
3. Test database connection: `railway run python -c "import sqlalchemy; print('OK')"`
4. Test Redis connection: `railway run redis-cli ping`

---

**You're ready to launch! 🚀**
