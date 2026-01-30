import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'scientific.db')

def migrate():
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Checking for 'model_signature' column in 'topics' table...")
        cursor.execute("PRAGMA table_info(topics)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'model_signature' not in columns:
            print("Adding 'model_signature' column...")
            cursor.execute("ALTER TABLE topics ADD COLUMN model_signature TEXT")
            conn.commit()
            print("Successfully added 'model_signature' column.")
        
        if 'specific_topic' not in columns:
            print("Adding 'specific_topic' column...")
            cursor.execute("ALTER TABLE topics ADD COLUMN specific_topic TEXT")
            conn.commit()
            print("Successfully added 'specific_topic' column.")
        else:
            print("'specific_topic' column already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
