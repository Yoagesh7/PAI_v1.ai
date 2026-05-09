# ✅ Testing Supabase on Vercel - Quick Guide

## Your Setup Status
✅ DATABASE_URL is set in Vercel  
✅ Code is deployed to Vercel  
✅ Supabase is configured in your app

Now let's verify everything works!

---

## Quick Test (2 minutes)

### 1️⃣ Go to Your Vercel App
Open: **https://pai-v1-ai.vercel.app**

### 2️⃣ Test Habits Persistence

**Test Case: Add Habit → Navigate Away → Return → Data Persists**

1. Click **Habits** in navigation
2. Click **Add Habit**
3. Enter: `Test Supabase Persistent`
4. Click **Save**
   - ✅ Should see: "Habit saved successfully" (or similar)
   - ❌ If error: Check Vercel logs
5. Go to **Home** or another page
6. Go back to **Habits**
7. ✅ **Your habit should be there!**
   - If ✅: Supabase is working!
   - If ❌: Check troubleshooting below

### 3️⃣ Test Knowledge Blocks

1. Click **Knowledge Blocks**
2. Click **Create Block**
3. Add title: `Test Supabase`
4. Add content: `This is a test for Supabase persistence`
5. Click **Save**
6. Navigate away and come back
7. ✅ **Block should still exist!**

### 4️⃣ Test Chat History

1. Click **Chat / AI Mentor**
2. Send a message: `Hello, testing Supabase`
3. Go to another page
4. Come back to Chat
5. ✅ **Your message should be in history!**

### 5️⃣ Test AI Tasks

1. Go to **Home**
2. Look at the tasks widget
3. Refresh the page
4. ✅ **Tasks should still be visible!**

---

## What Should Happen

### Before Supabase (SQLite - Broken) ❌
```
1. Add habit
2. Navigate away
3. Come back
4. ❌ Habit is gone (lost in ephemeral /tmp)
```

### After Supabase (PostgreSQL - Fixed) ✅
```
1. Add habit
2. Navigate away
3. Come back
4. ✅ Habit is still there (saved in Supabase)
```

---

## Troubleshooting

### Issue: Data still disappears

**Step 1: Check Vercel Deployment Status**
1. Go to https://vercel.com → pai-v1-ai
2. Click **Deployments**
3. Check latest deployment:
   - ✅ Should have green checkmark (Ready)
   - ⏳ If still building, wait for it to complete
   - ❌ If error/failed, check logs below

**Step 2: Check Vercel Logs for Errors**
1. In Vercel → Deployments → Latest deployment
2. Click **Logs**
3. Look for errors containing:
   - `DATABASE_URL`
   - `psycopg2`
   - `PostgreSQL`
   - `Connection refused`

**Common Errors:**
- `DATABASE_URL not set` → Re-add to Vercel env vars
- `Connection refused` → Supabase database might be offline
- `psycopg2 not installed` → Check requirements.txt includes `psycopg2-binary`

**Step 3: Check Supabase Status**
1. Go to https://supabase.com → Your Project
2. Look at "Database" status (top right)
3. Should be **Online** (green)
4. If ❌ offline, click to restart

**Step 4: Verify DATABASE_URL Format**

Your Supabase connection string should:
- ✅ Start with: `postgresql://`
- ✅ Include: `sslmode=require`
- ✅ No brackets `[` `]`
- ✅ No extra spaces

Example valid format:
```
postgresql://postgres.abcd1234:mypassword@db.abcd1234.supabase.co:5432/postgres?sslmode=require
```

**Step 5: Hard Refresh Browser**
```
Windows: Ctrl+Shift+R
Mac: Cmd+Shift+R
```

---

## Verify Data in Supabase

If data is persisting, you can verify it's in Supabase:

### Method 1: Supabase Dashboard

1. Go to https://supabase.com → Your Project
2. Click **SQL Editor**
3. Create new query and run:
   ```sql
   SELECT COUNT(*) as total_habits FROM habits;
   ```
4. Should return a number > 0 if you've added habits

### Method 2: Check Tables

1. In Supabase → **Table Editor**
2. Click **habits** table
3. ✅ You should see your test habit!

---

## Summary

| What to Test | Expected Result | Status |
|-------------|-----------------|--------|
| Add Habit | Saves successfully | ✅ or ❌ |
| Habit persists after navigation | Habit still there | ✅ or ❌ |
| Knowledge block persists | Block still there | ✅ or ❌ |
| Chat history persists | Messages still visible | ✅ or ❌ |
| AI tasks persist | Tasks after refresh | ✅ or ❌ |

If all show ✅, **Supabase is working perfectly!**

---

## Next Steps

### If Everything Works ✅
1. **Congratulations!** Data persistence is fixed
2. You can remove the localStorage fallback code (optional - it's still safe as backup)
3. Focus on your app features - data is now persistent!

### If Something Doesn't Work ❌
1. Check the troubleshooting steps above
2. Verify DATABASE_URL in Vercel is correct
3. Check Vercel and Supabase logs
4. Redeploy: `git push`

---

## Quick Redeploy if Needed

```bash
cd e:\PartnerAI
git push
```

Then wait ~2-3 minutes for Vercel deployment to complete.

---

**Questions?**
- Check Supabase docs: https://supabase.com/docs
- Check Vercel docs: https://vercel.com/docs
- Run verification script: `python verify_supabase_connection.py`

Your app is ready! 🚀
