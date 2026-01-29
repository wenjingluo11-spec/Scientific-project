
import sqlite3
import os

DB_PATH = "database/scientific.db"

if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS industry_news")
        conn.commit()
        conn.close()
        print("Successfully dropped industry_news table.")
    except Exception as e:
        print(f"Error dropping table: {e}")
else:
    print(f"Database file {DB_PATH} not found. Skipping drop.")
