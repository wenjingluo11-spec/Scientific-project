import sqlite3
import os

DB_PATH = "backend/database/scientific.db"

def migrate_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. It will be created when running the app.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Update agent_conversations table
        print("Migrating agent_conversations table...")
        try:
            cursor.execute("ALTER TABLE agent_conversations ADD COLUMN model_signature TEXT")
            print("Added model_signature column")
        except sqlite3.OperationalError:
            print("Column model_signature might already exist")

        try:
            cursor.execute("ALTER TABLE agent_conversations ADD COLUMN step_name TEXT")
            print("Added step_name column")
        except sqlite3.OperationalError:
            print("Column step_name might already exist")

        try:
            cursor.execute("ALTER TABLE agent_conversations ADD COLUMN input_context TEXT")
            print("Added input_context column")
        except sqlite3.OperationalError:
            print("Column input_context might already exist")

        # 2. Update topics table
        print("Migrating topics table...")
        try:
            cursor.execute("ALTER TABLE topics ADD COLUMN model_signature TEXT")
            print("Added model_signature column")
        except sqlite3.OperationalError:
            print("Column model_signature might already exist")

        # 3. Update industry_news table
        print("Migrating industry_news table...")
        try:
            cursor.execute("ALTER TABLE industry_news ADD COLUMN model_signature TEXT")
            print("Added model_signature column")
        except sqlite3.OperationalError:
            print("Column model_signature might already exist")

        # 4. Update competitors table
        print("Migrating competitors table...")
        try:
            cursor.execute("ALTER TABLE competitors ADD COLUMN model_signature TEXT")
            print("Added model_signature column")
        except sqlite3.OperationalError:
            print("Column model_signature might already exist")

        conn.commit()
        print("\nMigration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
