# 🚀 RECRUITER DEPLOYMENT - QUICK START

## Your Goal
Create a public link to share with recruiters in **15 minutes**.

**Final Link**: `https://autointern.vercel.app` (You'll get this)

---

## ⏱️ Timeline

```
0:00-5:00    Deploy Frontend → Vercel
5:00-10:00   Deploy Backend → Railway  
10:00-12:00  Connect them together
12:00-15:00  Test & prepare to share
```

---

## PART 1️⃣: Frontend (Vercel) - 5 Min

### If you have GitHub account:
```
1. Push code: git push
2. Go to vercel.com/new
3. Import your GitHub repo
4. Root directory: services/web/apps/dashboard
5. Click Deploy
6. ✅ Get public URL (write it down)
```

### If no GitHub:
```powershell
npm install -g vercel
cd services/web/apps/dashboard
vercel login
vercel --prod
```

**Expected result**: `https://autointern-xyz.vercel.app` 
(Try opening it - it will work but backend won't be connected yet)

---

## PART 2️⃣: Backend (Railway) - 10 Min

### Quick setup:
```
1. Go to railway.app
2. Login with GitHub
3. Create new project → from GitHub repo
4. Select AutoIntern repo
5. Set service root: services/api
6. Add variables:
   - ENVIRONMENT=production
   - DATABASE_URL=your_postgres_url (get from Railway)
7. Deploy
8. ✅ Get Railway URL (write it down)
```

**Expected result**: Railway generates a URL like `https://api-prod-123.railway.app`

### Check status:
Go to Railway dashboard → Your project → Logs
Should see: `"Application startup complete"`

---

## PART 3️⃣: Connect Them - 2 Min

Backend URL + Frontend URL = 🎉 Working app

### In Vercel:
```
1. Go to Vercel dashboard
2. Click AutoIntern project
3. Settings → Environment Variables
4. Add new:
   Name: NEXT_PUBLIC_API_URL
   Value: https://api-prod-123.railway.app (your Railway URL)
5. Save
6. Deployments → Click redeploy
7. Wait 30 seconds
```

---

## PART 4️⃣: Test - Use It!

1. Open your Vercel URL
2. Try these:
   - [ ] Page loads
   - [ ] Can log in
   - [ ] Can upload resume
   - [ ] Can search jobs
   - [ ] Mobile: install button appears
3. If errors: Check browser console (F12)

**Common issues:**
- Getting errors? Check Railway logs
- 404 errors? Railway URL needs `/api` prefix sometimes
- Timeout? Railway might be starting up

---

## PART 5️⃣: Share! - It's Done 🎉

```
YOUR RECRUITER LINK:
👉 https://autointern.vercel.app

Send to recruiters via:
  - Email
  - LinkedIn
  - WhatsApp
  - Twitter
```

**Email template:**
```
Hi [Name],

Check out AutoIntern - an AI job recommendation system I built.

🔗 https://autointern.vercel.app

Works on phone (you can install it) and desktop.
Built with: Next.js, FastAPI, AI/ML embeddings.

Let me know what you think!
```

---

## Environment Variables Needed

### For Railway backend:
```
ENVIRONMENT=production
DATABASE_URL=your_postgres_url
REDIS_URL=your_redis_url
JWT_SECRET=your_secret_key
MINIO_URL=your_minio_url
```

(Railway can auto-create some of these)

### For Vercel frontend:
```
NEXT_PUBLIC_API_URL=https://your-railway-domain
```

---

## Deployment Status Checklist

- [ ] Frontend URL obtained from Vercel
- [ ] Backend URL obtained from Railway
- [ ] API_URL added to Vercel env variables
- [ ] Vercel redeployed
- [ ] Can open app in browser
- [ ] Can log in
- [ ] Can use features
- [ ] Mobile install works
- [ ] Link shared with recruiters

---

## If Something Breaks

```
Error → What to Check
─────────────────────────────────────
App won't load → Vercel logs (Deployments → Function Logs)
API errors → Railway logs (Logs tab)
CORS errors → Backend CORS config needs Vercel URL
Timeout → Railway might be slow (wait 1 min)
Auth fails → Check JWT_SECRET matches
```

---

## Cleanup (Optional)

Remove old local deployment scripts:
```powershell
# You can delete these if you want
rm deploy-pwa.ps1
rm deploy-pwa.sh
```

They were for local phone testing. Now you have production links!

---

## What You Have Now 💪

```
✅ Production Frontend:  vercel.app
✅ Production Backend:   railway.app
✅ Shareable Link:       ONE URL for recruiters
✅ Phone installable:    PWA still works
✅ Offline support:      Still cached optimally
✅ Professional:         Production-grade deployment
```

---

## Next Level (Optional)

After recruiters love it:
- [ ] Add custom domain (yourdomain.com) - $10/year
- [ ] Set up monitoring/alerts
- [ ] Add Google Analytics
- [ ] Deploy to multiple regions

But for now: **You have a working link. That's enough!** 🚀

---

Start with Part 1 ⬆️
