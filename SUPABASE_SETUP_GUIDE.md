# ✅ Supabase DATABASE_URL Setup Guide

## Status: Your app is ready for Supabase!

The code is already configured to use Supabase PostgreSQL when `DATABASE_URL` environment variable is set in Vercel.

---

## Step 1: Verify DATABASE_URL is in Vercel ✅

Check your Vercel environment variables:

```bash
# Login to Vercel
vercel env list

# You should see DATABASE_URL listed
# If not, add it:
vercel env add DATABASE_URL
# Paste your Supabase connection string when prompted
```

Or use the web dashboard:
1. Go to https://vercel.com → Select your project
2. Settings → Environment Variables
3. Look for `DATABASE_URL` 
4. If missing, add:
   - **Name**: `DATABASE_URL`
   - **Value**: (Your Supabase PostgreSQL connection string)

---

## Step 2: How App Detects Supabase

When you deploy to Vercel, the app automatically:

1. **Checks for DATABASE_URL**
   ```python
   db_url = os.getenv("DATABASE_URL")  # Reads from Vercel env
   ```

2. **Uses PostgreSQL if detected**
   ```python
   if db_url and db_url.startswith("postgres"):
       import psycopg2
       conn = psycopg2.connect(db_url, sslmode='require')  # Connects to Supabase
   ```

3. **Falls back to SQLite if DATABASE_URL missing**
   ```python
   else:
       conn = sqlite3.connect(DB_NAME)  # Falls back to ephemeral /tmp
   ```

---

## Step 3: Get Your Supabase Connection String

### If you already have Supabase:

1. Go to https://supabase.com → Dashboard
2. Select your project
3. Click **Settings** → **Database**
4. Under "Connection string" select **"URI"**
5. Copy the connection string
   - It looks like: `postgresql://postgres.xxxxx:password@db.xxxxx.supabase.co:5432/postgres?sslmode=require`

### If you DON'T have Supabase yet:

1. Go to https://supabase.com → Click **Sign Up**
2. Create account (use GitHub login for faster setup)
3. Create a new project:
   - Name: `partnerai` (or your preference)
   - Region: Pick closest to your users
   - Password: Create strong password
   - Click **Create new project** (takes 1-2 minutes)
4. Once created, go to **Settings** → **Database**
5. Copy the PostgreSQL URI connection string

---

## Step 4: Add to Vercel

### Option A: Command Line (Fastest)
```bash
cd e:\PartnerAI
vercel env add DATABASE_URL
# Paste the connection string when prompted
# Choose: Production (or all environments)
```

### Option B: Web Dashboard
1. Go to https://vercel.com → Your Project
2. **Settings** → **Environment Variables**
3. Click **Add Environment Variable**
   - Name: `DATABASE_URL`
   - Value: (paste Supabase connection string)
   - Select checkboxes: Production, Preview, Development
4. Click **Save**

---

## Step 5: Redeploy to Vercel

### Important: Redeploy after adding DATABASE_URL!

```bash
# Push code and trigger Vercel deployment
git add .
git commit -m "Add Supabase verification"
git push
```

Or manually redeploy:
1. Go to https://vercel.com → Your Project
2. Click **Deployments**
3. Find the latest deployment
4. Click **...** → **Redeploy**
5. Wait for deployment to complete

---

## Step 6: Test Supabase on Vercel

Once deployment completes, test in your app:

### Test Habits Persistence:
1. Go to your Vercel app URL (e.g., https://yourapp.vercel.app)
2. Go to **Habits** page
3. **Add a habit** (e.g., "Test Supabase")
4. **Navigate to another page** (e.g., Home)
5. **Go back to Habits**
6. ✅ **Habit should still be there!** (Not lost)

### Test Knowledge Blocks:
1. Go to **Knowledge Blocks**
2. **Create a new block** with some content
3. **Navigate away** and come back
4. ✅ **Block should persist!**

### Test Chat History:
1. Go to **Chat**
2. **Send a message** to AI
3. **Go to another page** and come back
4. ✅ **Chat history should be there!**

### Test AI Tasks:
1. Go to **Home**
2. **Wait for AI to suggest tasks** (or manually verify in tasks widget)
3. **Refresh the page**
4. ✅ **Tasks should still appear!**

---

## Troubleshooting

### Problem: Data still disappears after adding DATABASE_URL

**Solution:**
1. Double-check DATABASE_URL in Vercel Settings
   - Make sure it's in **Production** environment
   - No extra spaces or brackets
   - Starts with `postgresql://`

2. Verify deployment completed
   - Go to Vercel → Deployments
   - Wait for green checkmark ✅
   - Should say "Ready"

3. Do a hard refresh
   ```
   Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
   ```

4. Check Vercel logs for errors
   - Vercel → Deployments → Latest → Logs
   - Look for DATABASE_URL or PostgreSQL errors

---

### Problem: "psycopg2 not installed" error

Your app has a fallback, but for better performance:

1. Check `requirements.txt` includes:
   ```
   psycopg2-binary>=2.8.6
   ```

2. If missing, add it:
   ```bash
   pip install psycopg2-binary
   echo "psycopg2-binary>=2.8.6" >> requirements.txt
   git add requirements.txt
   git commit -m "Add psycopg2 for PostgreSQL support"
   git push
   ```

---

### Problem: Connection string has special characters

If your Supabase password has special characters, they might need URL encoding:

Example:
- Password: `P@ss%word!`
- Should be: `P%40ss%25word%21`

Use this Python snippet to encode:
```python
import urllib.parse
password = "P@ss%word!"
encoded = urllib.parse.quote(password, safe='')
print(encoded)  # P%40ss%25word%21
```

---

## Verification Script

To verify locally before deploying:

```bash
cd e:\PartnerAI
python verify_supabase_connection.py
```

This will:
- ✅ Check if DATABASE_URL is configured
- ✅ Test PostgreSQL connection
- ✅ Test data persistence (save and retrieve a test user)

---

## How Data Flows Now

### Without Supabase (Before):
```
User Action → Vercel (Flask) → /tmp/partnerai_data.db (SQLite)
                              ↓ (lost when request ends)
                              ❌ Data disappeared
```

### With Supabase (Now):
```
User Action → Vercel (Flask) → Supabase PostgreSQL (Persistent)
                              ↓ (data stays in database)
                              ✅ Data persists across requests
```

---

## Summary

| Feature | Before (SQLite) | After (Supabase) |
|---------|-----------------|------------------|
| Habits | ❌ Lost between requests | ✅ Persistent |
| Knowledge Blocks | ❌ Lost between requests | ✅ Persistent |
| Chat History | ❌ Disappeared on page refresh | ✅ Persistent |
| AI Tasks | ❌ Disappeared on refresh | ✅ Persistent |
| Multiple Users | ❌ Conflicts (shared /tmp) | ✅ Isolated by user |
| Reliability | ⚠️ Unreliable | ✅ Highly reliable |

---

## Next Steps

1. ✅ Verify DATABASE_URL is in Vercel environment variables
2. ✅ Redeploy to Vercel (git push)
3. ✅ Wait for deployment to complete (green checkmark)
4. ✅ Test your app - data should now persist!
5. ⚠️ If data still disappears, check Vercel logs

---

## Have Questions?

- **Supabase docs**: https://supabase.com/docs/guides/database
- **Vercel env vars**: https://vercel.com/docs/concepts/projects/environment-variables
- **PostgreSQL basics**: https://www.postgresql.org/docs/

Your app is ready! 🚀
