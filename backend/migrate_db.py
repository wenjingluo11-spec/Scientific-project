import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'scientific.db')

def migrate():
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Migrate 'topics' table
        print("Checking 'topics' table...")
        cursor.execute("PRAGMA table_info(topics)")
        topic_columns = [column[1] for column in cursor.fetchall()]
        
        topic_migrations = [
            ('model_signature', 'TEXT'),
            ('specific_topic', 'TEXT'),
        ]
        
        for col_name, col_type in topic_migrations:
            if col_name not in topic_columns:
                print(f"Adding '{col_name}' column to 'topics'...")
                cursor.execute(f"ALTER TABLE topics ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"Successfully added '{col_name}' column.")
            else:
                print(f"'{col_name}' column already exists in 'topics'.")
        
        # Migrate 'papers' table
        print("\nChecking 'papers' table...")
        cursor.execute("PRAGMA table_info(papers)")
        paper_columns = [column[1] for column in cursor.fetchall()]
        
        paper_migrations = [
            ('topic_ids', 'TEXT'),
            ('detailed_scores', 'TEXT'),
        ]
        
        for col_name, col_type in paper_migrations:
            if col_name not in paper_columns:
                print(f"Adding '{col_name}' column to 'papers'...")
                cursor.execute(f"ALTER TABLE papers ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"Successfully added '{col_name}' column.")
            else:
                print(f"'{col_name}' column already exists in 'papers'.")
        
        # Migrate 'agent_conversations' table
        print("\nChecking 'agent_conversations' table...")
        cursor.execute("PRAGMA table_info(agent_conversations)")
        conversation_columns = [column[1] for column in cursor.fetchall()]
        
        conversation_migrations = [
            ('model_signature', 'TEXT'),
            ('step_name', 'TEXT'),
            ('input_context', 'TEXT'),
        ]
        
        for col_name, col_type in conversation_migrations:
            if col_name not in conversation_columns:
                print(f"Adding '{col_name}' column to 'agent_conversations'...")
                cursor.execute(f"ALTER TABLE agent_conversations ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"Successfully added '{col_name}' column.")
            else:
                print(f"'{col_name}' column already exists in 'agent_conversations'.")
                
        print("\nMigration completed successfully!")
            
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
