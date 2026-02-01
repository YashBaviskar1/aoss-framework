import os
from database import engine, SessionLocal
from sqlalchemy import text

def add_column():
    print("Attempting to add 'server_metadata' column to 'servers' table...")
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE servers ADD COLUMN IF NOT EXISTS server_metadata JSON DEFAULT '{}'"))
            conn.commit()
        print("✅ Success: Column added or already exists.")
    except Exception as e:
        print(f"❌ Error adding column: {e}")

if __name__ == "__main__":
    add_column()
