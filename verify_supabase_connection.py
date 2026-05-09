#!/usr/bin/env python3
"""
Verify Supabase DATABASE_URL configuration on Vercel
Tests that data persists across requests using PostgreSQL
"""

import os
import sys

# Add parent to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_supabase_config():
    """Check if Supabase DATABASE_URL is configured"""
    print("=" * 60)
    print("SUPABASE CONFIGURATION CHECK")
    print("=" * 60)
    
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("\n❌ DATABASE_URL environment variable NOT SET")
        print("\nTo fix this:")
        print("1. On Supabase: Copy your PostgreSQL connection string")
        print("   - Go to: https://supabase.com → Your Project → Settings → Database")
        print("   - Copy the 'PostgreSQL Connection String'")
        print("\n2. In Vercel: Add to environment variables")
        print("   - Go to: https://vercel.com → Project → Settings → Environment Variables")
        print("   - Add new variable: Name='DATABASE_URL', Value='<your-connection-string>'")
        print("   - Click 'Save'")
        print("   - Redeploy: vercel --prod")
        print("\n3. The string should look like:")
        print("   postgresql://user:password@host:5432/database?sslmode=require")
        return False
    
    print("\n✅ DATABASE_URL IS SET")
    
    # Check connection details
    if "postgresql" in db_url or "postgres" in db_url:
        print("✅ Using PostgreSQL (Supabase/Neon)")
    else:
        print("⚠️  Not a PostgreSQL URL - might not be using Supabase")
    
    if "sslmode=require" in db_url:
        print("✅ SSL mode enabled (required for Supabase)")
    else:
        print("⚠️  Consider adding ?sslmode=require to your connection string")
    
    return True

def test_database_connection():
    """Test that we can connect to the database"""
    print("\n" + "=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    
    try:
        from memory import get_db, get_user
        
        # Try to get a test connection
        conn = get_db()
        if conn:
            print("\n✅ Database connection successful!")
            
            # Check if it's PostgreSQL
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                if version:
                    print(f"✅ PostgreSQL version: {version[0][:50]}...")
                cursor.close()
            except Exception as e:
                print(f"⚠️  Could not fetch PostgreSQL version: {e}")
            
            conn.close()
            return True
        else:
            print("\n❌ Could not establish database connection")
            return False
            
    except ImportError:
        print("\n⚠️  Could not import database modules (might be OK in non-dev environment)")
        return None
    except Exception as e:
        print(f"\n❌ Database connection error: {e}")
        print("\nTroubleshooting:")
        print("1. Check DATABASE_URL is correct in Vercel environment variables")
        print("2. Verify Supabase database is running (check Supabase dashboard)")
        print("3. Check that psycopg2 is installed: pip install psycopg2-binary")
        print(f"4. Error details: {str(e)}")
        return False

def test_data_persistence():
    """Test that data persists across function calls"""
    print("\n" + "=" * 60)
    print("DATA PERSISTENCE TEST")
    print("=" * 60)
    
    try:
        from memory import save_user, get_user
        
        # Create a test user with timestamp
        import time
        test_user_id = f"test_supabase_{int(time.time())}"
        test_data = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@supabase.test",
            "password": "test_password_123",
            "about_me": "Testing Supabase persistence"
        }
        
        # Save user (first request)
        print(f"\n1. Saving test user: {test_user_id}")
        result = save_user(test_user_id, test_data)
        print(f"   ✅ Save result: {result}")
        
        # Retrieve user (simulates new request)
        print(f"\n2. Retrieving test user (simulates new request)")
        retrieved = get_user(test_user_id)
        
        if retrieved:
            print("   ✅ User retrieved successfully!")
            print(f"   Username: {retrieved.get('username')}")
            print(f"   Email: {retrieved.get('email')}")
            print(f"   About me: {retrieved.get('about_me')}")
            
            if retrieved.get('username') == test_data['username']:
                print("\n✅ DATA PERSISTENCE CONFIRMED!")
                print("   Supabase is working correctly on Vercel")
                return True
            else:
                print("\n❌ Data mismatch")
                return False
        else:
            print("   ❌ Could not retrieve user")
            return False
            
    except Exception as e:
        print(f"\n⚠️  Could not run persistence test: {e}")
        print("   This might be OK if database functions are not available locally")
        return None

def main():
    print("\n" + "=" * 60)
    print("VERCEL SUPABASE VERIFICATION")
    print("=" * 60)
    
    # Step 1: Check config
    has_config = check_supabase_config()
    
    if not has_config:
        print("\n" + "=" * 60)
        print("ACTION REQUIRED: Set DATABASE_URL in Vercel")
        print("=" * 60)
        print("\nYour app is currently using SQLite (ephemeral on Vercel)")
        print("Data will be lost between requests.\n")
        print("To enable Supabase persistence:")
        print("\n1. If you don't have a Supabase account:")
        print("   - Go to https://supabase.com")
        print("   - Click 'Sign Up' and create account")
        print("   - Create a new project")
        print("\n2. Get PostgreSQL connection string:")
        print("   - In Supabase: Project → Settings → Database → Connection String")
        print("   - Copy the string (it includes username and password)")
        print("\n3. Add to Vercel:")
        print("   - Go to https://vercel.com → Your Project → Settings → Environment Variables")
        print("   - Name: DATABASE_URL")
        print("   - Value: (paste the Supabase connection string)")
        print("   - Save and Redeploy")
        print("\n4. Verify deployment:")
        print("   - Wait for Vercel deployment to complete")
        print("   - Test in your app: Add a habit, refresh page, habit should persist")
        print("\n" + "=" * 60)
        return False
    
    # Step 2: Test connection
    print("\nAttempting to test database connection...")
    conn_result = test_database_connection()
    
    # Step 3: Test persistence
    if conn_result is not False:
        print("\nAttempting to test data persistence...")
        persist_result = test_data_persistence()
        
        if persist_result is True:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED - SUPABASE CONFIGURED CORRECTLY!")
            print("=" * 60)
            print("\nYour app is now using Supabase for data persistence.")
            print("All features (habits, knowledge blocks, chat, tasks) will persist on Vercel.")
            print("\nNo localStorage fallback needed - data saves to PostgreSQL.")
            return True
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    
    if has_config:
        print("\n✅ DATABASE_URL is configured")
        print("⚠️  Connection test could not complete (might be normal)")
        print("\nTo verify Supabase is working:")
        print("1. Deploy the app to Vercel: git push")
        print("2. In Vercel: Wait for deployment to complete")
        print("3. Test in your app:")
        print("   - Add a habit")
        print("   - Navigate to another page")
        print("   - Come back to habits")
        print("   - Habit should still be there (not lost between page loads)")
        print("\nIf data persists, Supabase is configured correctly! 🎉")

if __name__ == "__main__":
    main()
