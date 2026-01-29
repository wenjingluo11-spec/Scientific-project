import sqlite3
import os

DB_PATH = "backend/database/scientific.db"

def migrate_db_topic_rec():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. It will be created when running the app.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Update topic_recommendations table
        print("Migrating topic_recommendations table...")
        try:
            cursor.execute("ALTER TABLE topic_recommendations ADD COLUMN model_signature TEXT")
            print("Added model_signature column")
        except sqlite3.OperationalError:
            print("Column model_signature might already exist")

        conn.commit()
        print("\nMigration for TopicRecommendation completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db_topic_rec()
