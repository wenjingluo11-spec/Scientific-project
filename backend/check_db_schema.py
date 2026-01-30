
import sqlite3

db_path = './database/scientific.db'
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(industry_news)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Columns in industry_news: {columns}")
    
    if 'model_signature' in columns:
        print("✅ model_signature exists.")
    else:
        print("❌ model_signature MISSING!")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
