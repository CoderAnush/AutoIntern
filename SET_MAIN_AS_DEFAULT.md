# Set Main as Default Branch on GitHub

## Quick Steps (2 min)

### Step 1: Go to GitHub Repository Settings
1. Open: https://github.com/CoderAnush/AutoIntern
2. Click **Settings** (top right, next to "Actions")
3. Left sidebar → Click **Branches**

### Step 2: Change Default Branch
1. Under "Default branch" section
2. Click the dropdown (likely shows `dev/init` or `master`)
3. Select **`main`**
4. Click **Update** button
5. Confirm warning (if any)

### Step 3: Verify Success
✅ You should see: **Default branch is now `main`**

---

## Visual Guide

```
GitHub Repo
    ↓
[Settings] button (top right)
    ↓
Left sidebar: [Branches]
    ↓
"Default branch" section
    ↓
Dropdown showing: dev/init ← current
    ↓
Click dropdown → Select: main
    ↓
[Update] button
    ↓
✅ Default branch changed to main
```

---

## What This Does

After changing:

```
BEFORE                      AFTER
├─ Cloning repo             ├─ Cloning repo
│  → Gets: dev/init         │  → Gets: main ✅
│                           │
├─ Vercel deploys           ├─ Vercel deploys
│  → Looks for: dev/init    │  → Looks for: main ✅
│                           │
└─ GitHub defaults to       └─ GitHub defaults to
   dev/init branch             main branch ✅
```

---

## After You Change It

Vercel will automatically:
1. ✅ Clone from `main` (next time)
2. ✅ Find your PWA code
3. ✅ Build successfully
4. ✅ Deploy to production

---

## Verify It Worked

Go back to: https://github.com/CoderAnush/AutoIntern

You should see on the page:
```
🔓 main (default)  [branch icon]
```

Instead of:
```
🔓 dev/init  [branch icon]
```

---

## Then Redeploy on Vercel

Once default branch is `main`:

1. Go to **Vercel Dashboard**
2. Your AutoIntern project
3. **Deployments** → Click **Redeploy**
4. Watch it deploy from `main` ✅

---

**Takes 2 minutes, fixes everything!** 🚀
