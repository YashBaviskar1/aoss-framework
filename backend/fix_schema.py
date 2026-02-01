from database import engine
from sqlalchemy import text

def migrate():
    print("Starting migration...")
    try:
        with engine.connect() as conn:
            print("Adding 'agent_summary' column to 'execution_logs'...")
            conn.execute(text("ALTER TABLE execution_logs ADD COLUMN IF NOT EXISTS agent_summary TEXT;"))
            conn.commit()
            print("Migration successful! Column 'agent_summary' added.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
