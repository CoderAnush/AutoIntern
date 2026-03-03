# 📱 AutoIntern PWA - Quick Reference

## ⚡ TL;DR - Get It Running in 2 Minutes

### Windows (PowerShell)
```powershell
# Run this command in the root AutoIntern folder
.\deploy-pwa.ps1
```

### Mac/Linux (Bash)
```bash
# Run this command in the root AutoIntern folder
bash deploy-pwa.sh
```

### Then:
1. **On your phone**, open a browser
2. Go to **http://YOUR_IP:3000** (shown in terminal)
3. **Android**: Menu → Install app
4. **iPhone**: Share → Add to Home Screen
5. ✅ Done! App installed on your phone

---

## 📱 Installation by Platform

### 🤖 Android Phone (Google Chrome)

**Method 1: Install Prompt**
1. Open Chrome on your phone
2. Go to `http://YOUR_IP:3000`
3. Wait 10 seconds
4. Tap the **menu button** (⋮ at top right)
5. Tap **"Install app"** or **"Add to Home Screen"**
6. Confirm by tapping **"Install"**

**Method 2: Smart Banner**
- A banner may pop up automatically
- Tap the **"Install"** button
- Done!

**Method 3: Address Bar**
- URL bar shows install icon on the right
- Tap that icon to install

### 🍎 iPhone / iPad (Safari)

1. Open Safari on your iPhone/iPad
2. Go to `http://YOUR_IP:3000`
3. Tap the **Share button** (↗️ at bottom)
4. Scroll down and tap **"Add to Home Screen"**
5. Give it a name (default: "AutoIntern")
6. Tap **"Add"** in top right
7. ✅ You'll see it on your home screen!

### 💻 Windows/Mac Desktop

**Chrome or Edge:**
1. Go to `http://localhost:3000`
2. Click the **install icon** (in URL bar)
3. Click **"Install"**
4. It appears in your taskbar

**Keyboard shortcut:**
- Press `Ctrl+Shift+M` (Chrome/Edge)
- Or from menu → Create Shortcut

---

## 🔧 What's Installed?

### On Your Phone's Home Screen
- ✅ **App icon** (custom AutoIntern icon)
- ✅ **App name** - "AutoIntern"
- ✅ **Full-screen experience** - no browser UI
- ✅ **Instant loading** - cached from first visit
- ✅ **Offline support** - works without internet

### How It Works
```
Your Phone
    ↓
┌─────────────────┐
│ AutoIntern App  │
│   (Installed)   │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Service Worker  │  ← Handles offline
│  (Background)   │
└────────┬────────┘
         ↓
┌─────────────────┐
│  Local Cache    │  ← Stores data
│  (Phone Storage)│
└────────┬────────┘
         ↓
┌─────────────────┐
│   API Server    │  ← Your backend
│ (localhost:8000)│
└─────────────────┘
```

---

## 🌐 Network Setup

### If Backend is on Same Computer

Edit `.env.local` in your frontend directory:
```env
NEXT_PUBLIC_API_URL=http://YOUR_IP:8000
```

**Get your IP:**
- **Windows**: `ipconfig` → Look for "IPv4 Address"
- **Mac**: `ifconfig` → Look for "inet"
- **Linux**: `hostname -I`

Example: `http://192.168.1.5:8000`

### If Backend is Deployed (Cloud)

```env
NEXT_PUBLIC_API_URL=https://api.autointern.app
```

---

## ✅ Verify PWA is Working

### In Browser Console
```javascript
// Check if Service Worker is registered
navigator.serviceWorker.getRegistrations().then(regs => {
  console.log('Service Workers:', regs);
});

// Check if app is installed
if (window.matchMedia('(display-mode: standalone)').matches) {
  console.log('✅ App is installed!');
} else {
  console.log('❌ App is NOT installed yet');
}

// Check cache size
caches.keys().then(names => {
  console.log('Cache names:', names);
});
```

### On Your Phone
**Android:**
- Open app
- Press **Settings** → **Apps** → **AutoIntern**
- Should show as separate app (not using Chrome)

**iPhone:**
- Open app
- No Safari address bar should be visible
- Should look like a native app

---

## 🔌 Connection Modes

### Online
- ✅ Syncs with API server
- ✅ Fetches latest jobs
- ✅ Uploads resumes
- ✅ Updates recommendations
- ✅ Auto-caches responses

### Offline
- ✅ Shows cached pages
- ✅ Shows cached jobs
- ✅ Shows cached resumes
- ✅ Navigates locally
- ❌ Cannot login
- ❌ Cannot upload files
- ❌ Cannot fetch new data

---

## 🚀 Development vs Production

### Development Mode
```bash
npm run dev
```
- Service Worker **disabled** (easier debugging)
- Full browser DevTools available
- Auto-refresh on code changes
- No caching issues

### Production Mode
```bash
npm run build
npm start
```
- Service Worker **enabled** (full PWA)
- Optimized bundle size
- Full offline support
- Cached assets

### Important Notes
- Development: Service Worker is **DISABLED** (set in next.config.js)
- Build for production to test offline features
- Use `npm run build && npm start` to test PWA locally

---

## 🐛 Troubleshooting

### "Install App" Button Not Showing

```
Problem: I don't see an install option

Solutions:
1. Wait 10+ seconds (Service Worker needs time to register)
2. Refresh the page (Ctrl+Shift+R on desktop, Cmd+Shift+R on Mac)
3. Check that you're using HTTPS or localhost
4. Try: Menu → More tools → Create Shortcut
5. Clear cache: Settings → Privacy → Clear browsing data
6. Use Chrome (has best PWA support)
```

### App Won't Go Offline

```
Problem: App still tries to connect when offline

Solutions:
1. Verify Service Worker is running:
   DevTools → Application → Service Workers
2. Check if it says "activated and running"
3. Try: Clear site data and reinstall
4. Check cache preferences in next.config.js
5. Reload page while offline to trigger offline page
```

### Can't Connect to API

```
Problem: "Cannot connect to backend"

Solutions:
1. Check NEXT_PUBLIC_API_URL in .env.local
2. Verify backend is running: curl http://localhost:8000/health
3. Check IP address (use your machine IP, not localhost)
4. Verify firewall allows connections
5. Ensure phone is on same WiFi network
6. Check API CORS headers
```

### Icons Look Blurry or Wrong

```
Problem: App icon doesn't look right

Solutions:
1. Clear phone cache: Settings → Apps → AutoIntern → Storage → Clear Cache
2. Uninstall and reinstall the app
3. Wait a few minutes (system caches icons)
4. Try different icon size (192x192 is minimum for home screen)
5. Ensure PNG format (not JPEG)
```

---

## 📊 Performance Tips

### Reduce Cache Size
```javascript
// In browser console
caches.open('autointern-v1').then(cache => {
  cache.keys().then(requests => {
    console.log(requests.length, 'items cached');
  });
});
```

### Force Update Cache
```javascript
// In browser console
caches.delete('autointern-v1').then(() => {
  location.reload();
});
```

### Check Storage Usage
**Android:**
- Settings → Apps → AutoIntern → Storage
- Shows cache usage

**iPhone:**
- Settings → General → iPhone Storage → AutoIntern
- Shows app size

---

## 🎯 Next Steps

### 1. Local Testing (5 minutes)
```bash
cd services/web/apps/dashboard
npm install
npm run dev
```

### 2. Test on Phone
- Open `http://YOUR_IP:3000` on phone
- Install as app
- Test offline mode

### 3. Connect Backend
- Update `.env.local` with API URL
- Test login and job search

### 4. Deploy to Production
- Choose platform: Vercel, Railway, Render, etc.
- Set `NEXT_PUBLIC_API_URL` environment variable
- Deploy and share link with users

### 5. Monitor & Optimize
- Check cache hit rates
- Monitor performance
- Update as needed

---

## 📞 Resources

- **[PWA Checklist](https://web.dev/pwa-checklist/)**
- **[Service Worker Guide](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)**
- **[Next.js PWA](https://github.com/shadowwalker/next-pwa)**
- **[Web Manifest Spec](https://www.w3.org/TR/appmanifest/)**

---

## 🎉 You're All Set!

Your AutoIntern app is ready to install on any phone. Go ahead and:

1. ✅ Run the deployment script
2. ✅ Open the app on your phone
3. ✅ Install as home screen app
4. ✅ Enjoy your AI job recommendation platform!

**Questions?** Check the full guide: `PWA_DEPLOYMENT_GUIDE.md`
