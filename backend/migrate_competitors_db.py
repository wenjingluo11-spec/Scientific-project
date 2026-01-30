
import sqlite3

db_path = './database/scientific.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column exists first to avoid error
    cursor.execute("PRAGMA table_info(competitors)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'model_signature' not in columns:
        print("Adding model_signature column to competitors table...")
        cursor.execute("ALTER TABLE competitors ADD COLUMN model_signature VARCHAR(100)")
        conn.commit()
        print("✅ Column added successfully.")
    else:
        print("Column already exists.")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
