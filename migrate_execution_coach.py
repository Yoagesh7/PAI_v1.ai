"""
Execution Coach - Database Migration
Creates tables for execution planning and tracking
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from memory import get_db, init_db


def migrate_execution_coach():
    """Create execution coach database tables"""
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Determine ID type based on database
        is_pg = os.getenv("DATABASE_URL") is not None or "psycopg" in str(type(conn)).lower()
        id_type_ai = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"

        print("Creating Execution Coach tables...")

        # 1. execution_plans - stores daily plans
        try:
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS execution_plans (
                id {id_type_ai},
                user_id INTEGER NOT NULL,
                plan_date TEXT NOT NULL,
                
                -- Plan content
                top_priorities TEXT,  -- JSON array of priority tasks
                time_blocks TEXT,     -- JSON array of time blocks
                current_block_id INTEGER,
                do_now_task TEXT,     -- JSON
                suggested_focus_duration INTEGER DEFAULT 25,
                
                -- Metadata
                coaching_message TEXT,
                total_planned_minutes INTEGER DEFAULT 0,
                estimated_completion_rate REAL DEFAULT 0.0,
                
                -- Status
                is_completed INTEGER DEFAULT 0,
                actual_completion_rate REAL,
                
                created_at TEXT,
                updated_at TEXT,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_plans_user_date ON execution_plans(user_id, plan_date)")
            print("✅ execution_plans table created")
        except Exception as e:
            print(f"⚠️  execution_plans table: {e}")

        # 2. execution_blocks - individual time blocks within a plan
        try:
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS execution_blocks (
                id {id_type_ai},
                plan_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                
                -- Block details
                task_id INTEGER,  -- Reference to task if applicable
                task_title TEXT,
                block_type TEXT,  -- focus, work, habit, break, review
                
                -- Timing
                start_time TEXT,   -- HH:MM format
                end_time TEXT,     -- HH:MM format
                duration_minutes INTEGER,
                
                -- Status
                priority TEXT,     -- high, medium, low
                status TEXT DEFAULT 'scheduled',  -- scheduled, active, completed, skipped
                
                -- Completion
                completed_at TEXT,
                actual_duration_minutes INTEGER,
                completion_notes TEXT,
                
                created_at TEXT,
                
                FOREIGN KEY (plan_id) REFERENCES execution_plans(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_blocks_plan ON execution_blocks(plan_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_blocks_status ON execution_blocks(user_id, status)")
            print("✅ execution_blocks table created")
        except Exception as e:
            print(f"⚠️  execution_blocks table: {e}")

        # 3. execution_events - user interactions with execution system
        try:
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS execution_events (
                id {id_type_ai},
                user_id INTEGER NOT NULL,
                
                event_type TEXT,  -- plan_generated, block_started, block_completed, plan_rebuilt, recovery_initiated, recovery_completed
                
                -- Event context
                plan_id INTEGER,
                block_id INTEGER,
                
                -- Data
                event_data TEXT,  -- JSON with details
                
                timestamp TEXT,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (plan_id) REFERENCES execution_plans(id)
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_events_user_date ON execution_events(user_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_events_type ON execution_events(event_type)")
            print("✅ execution_events table created")
        except Exception as e:
            print(f"⚠️  execution_events table: {e}")

        # 4. execution_preferences - user preferences for execution coach
        try:
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS execution_preferences (
                id {id_type_ai},
                user_id INTEGER NOT NULL UNIQUE,
                
                -- Schedule preferences
                chronotype TEXT DEFAULT 'standard',  -- morning_person, night_owl, bimodal, standard
                work_time_preference TEXT,  -- e.g., "09:00-17:00"
                free_time_preference TEXT,  -- e.g., "18:00-22:00"
                
                -- Task preferences
                task_style TEXT DEFAULT 'mixed',  -- one_big_task, many_small_tasks, mixed
                preferred_focus_duration INTEGER DEFAULT 25,  -- Pomodoro duration
                
                -- Message preferences
                preferred_message_tone TEXT DEFAULT 'supportive',  -- direct, supportive, motivational
                enable_notifications INTEGER DEFAULT 1,
                
                -- Recovery preferences
                auto_suggest_recovery INTEGER DEFAULT 1,
                recovery_mode_threshold INTEGER DEFAULT 40,  -- momentum score below this triggers recovery
                
                -- Pomodoro preferences
                break_after_focus INTEGER DEFAULT 1,
                pomodoro_break_minutes INTEGER DEFAULT 5,
                
                created_at TEXT,
                updated_at TEXT,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_prefs_user ON execution_preferences(user_id)")
            print("✅ execution_preferences table created")
        except Exception as e:
            print(f"⚠️  execution_preferences table: {e}")

        # 5. execution_reflections - user reflections on daily execution
        try:
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS execution_reflections (
                id {id_type_ai},
                user_id INTEGER NOT NULL,
                plan_date TEXT NOT NULL,
                
                -- What went well
                went_well TEXT,
                
                -- What was challenging
                challenges TEXT,
                
                -- What to improve
                improvements TEXT,
                
                -- Mood/energy
                energy_level INTEGER,  -- 1-5 scale
                focus_quality INTEGER,  -- 1-5 scale
                
                -- Metrics
                tasks_completed INTEGER DEFAULT 0,
                tasks_missed INTEGER DEFAULT 0,
                habits_completed INTEGER DEFAULT 0,
                focus_sessions INTEGER DEFAULT 0,
                
                created_at TEXT,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_reflections_user_date ON execution_reflections(user_id, plan_date)")
            print("✅ execution_reflections table created")
        except Exception as e:
            print(f"⚠️  execution_reflections table: {e}")

        # 6. execution_recovery_plans - recovery plans generated
        try:
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS execution_recovery_plans (
                id {id_type_ai},
                user_id INTEGER NOT NULL,
                plan_date TEXT NOT NULL,
                
                -- Recovery components
                must_do_task TEXT,  -- JSON
                easy_win_task TEXT,  -- JSON
                streak_protecting_habit TEXT,  -- JSON
                focus_sprint TEXT,  -- JSON
                
                -- Recovery status
                recovery_message TEXT,
                estimated_recovery_time INTEGER,
                next_checkpoint TEXT,
                
                -- Tracking
                created_at TEXT,
                activated_at TEXT,
                completed_at TEXT,
                
                is_successful INTEGER DEFAULT 0,
                
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recovery_plans_user_date ON execution_recovery_plans(user_id, plan_date)")
            print("✅ execution_recovery_plans table created")
        except Exception as e:
            print(f"⚠️  execution_recovery_plans table: {e}")

        conn.commit()
        print("\n✅ All Execution Coach tables created successfully!")


if __name__ == "__main__":
    print("=" * 60)
    print("Execution Coach Database Migration")
    print("=" * 60)
    
    try:
        # First initialize main DB if needed
        init_db()
        print("\n✅ Main database initialized\n")
        
        # Then run execution coach migration
        migrate_execution_coach()
        print("\n✅ Execution Coach migration complete!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
