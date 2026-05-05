<!-- VERCEL FIXES GUIDE -->

# 🔧 PartnerAI Vercel Deployment Fix Guide

## Problem
After deploying to Vercel, you're getting:
- ❌ **HTTP 500 error when adding habits**
- ❌ **Knowledge blocks not saving**

## Root Cause
Vercel's serverless environment has an **ephemeral filesystem**. SQLite data stored in `/tmp` gets **wiped after each request**. That's why data isn't persisting!

---

## ✅ Solution: Use Vercel KV (Recommended - 5 minutes)

### Step 1: Add Vercel KV to Your Project
1. Go to your Vercel Dashboard
2. Select your PartnerAI project
3. Go to **Storage** tab
4. Click **Create Database**
5. Select **Vercel KV** (Redis)
6. Name it something like `partnerai-kv`
7. Click **Create**

### Step 2: Get Your KV Credentials
1. After KV is created, click on it
2. Go to **.env.local** tab
3. Copy the following variables:
   - `KV_REST_API_URL`
   - `KV_REST_API_TOKEN`

### Step 3: Add Environment Variables to Vercel
1. Go to your Vercel project **Settings**
2. Go to **Environment Variables**
3. Add both variables:
   ```
   KV_REST_API_URL=<paste_your_url>
   KV_REST_API_TOKEN=<paste_your_token>
   ```
4. Click **Save**

### Step 4: Install Redis Package
In your project root, add to `requirements.txt`:
```
redis
```

Or run:
```bash
pip install redis
```

### Step 5: Redeploy
Push your changes to trigger a new deployment:
```bash
git add .
git commit -m "Add Vercel KV support"
git push
```

Vercel will automatically detect the new environment variables and redeploy.

---

## ✅ Alternative Solution: Use PostgreSQL (Better for Production)

If you want more control, use a hosted PostgreSQL database:

### Option A: Vercel Postgres (integrated)
1. In Vercel Dashboard, go to **Storage** → **Create Database**
2. Select **Postgres**
3. Follow the setup
4. Copy the `DATABASE_URL` environment variable

### Option B: Neon, Supabase, or Railway
1. Create a free PostgreSQL database
2. Get your connection string
3. Add to Vercel environment as `DATABASE_URL`

The app will automatically use PostgreSQL if `DATABASE_URL` is set.

---

## 🧪 Verify the Fix

After deployment, test by:
1. Go to your deployed app
2. Add a new habit
3. Go to another page and return
4. **Habit should still be there** ✅

---

## ⚡ Quick Reference: Priority Order

The code checks for persistence in this order:

1. **PostgreSQL** (`DATABASE_URL` env var) → ✅ Best
2. **Vercel KV** (`KV_REST_API_URL`) → ✅ Recommended for Vercel
3. **SQLite** (Local file) → ✅ Good for development
4. **In-memory** (`:memory:`) → ❌ No persistence!

---

## 📋 Checklist

- [ ] Added KV (or PostgreSQL) to Vercel
- [ ] Copied environment variables
- [ ] Updated `requirements.txt` if using KV
- [ ] Pushed changes to trigger redeploy
- [ ] Verified deployment completed
- [ ] Tested adding a habit (should persist)
- [ ] Tested creating knowledge blocks (should save)

---

## 🆘 Still Having Issues?

### Check 1: Verify Environment Variables
Go to Vercel Settings → Environment Variables and confirm:
- Variables are actually saved
- Variable names match exactly (case-sensitive!)

### Check 2: Check Logs
In Vercel Deployments tab, view logs for error messages:
- Look for "Connection refused" → KV not configured
- Look for "redis library not found" → redis not in requirements.txt

### Check 3: Local Testing
Test locally to confirm the app works:
```bash
python web/app.py
```

Then add a habit locally - if it works locally but not on Vercel, it's an environment variable issue.

---

## 💡 Notes

- **KV Pricing**: Free tier includes 1000 commands/day. Excellent for hobby projects.
- **PostgreSQL Pricing**: Vercel Postgres and other providers have free tiers too.
- **Data is instantly synced** once you set up KV/PostgreSQL - no waiting.
- The code automatically falls back to SQLite if KV fails, so it won't break.

---

Good luck! 🚀 Let me know if you need more help!
