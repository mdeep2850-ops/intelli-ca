import sqlite3
import os

DB_PATH = "sql_app.db"

def migrate():
    print("Starting migration...")
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} does not exist. Migration not needed.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if indexing_status already exists in document_elements
        cursor.execute("PRAGMA table_info(document_elements)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "indexing_status" not in columns:
            print("Adding indexing_status column to document_elements...")
            cursor.execute("ALTER TABLE document_elements ADD COLUMN indexing_status VARCHAR(50) DEFAULT 'PENDING'")
        else:
            print("indexing_status column already exists.")

        if "is_chunked" in columns:
            print("Note: SQLite does not support dropping columns easily, leaving is_chunked intact.")

        # Create chunks table if it does not exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id VARCHAR PRIMARY KEY,
                chunk_id VARCHAR,
                element_id INTEGER,
                document_id INTEGER,
                content TEXT,
                content_hash VARCHAR,
                chunk_index INTEGER,
                metadata JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                indexing_status VARCHAR(50) DEFAULT 'PENDING',
                FOREIGN KEY(element_id) REFERENCES document_elements(id) ON DELETE CASCADE,
                FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_chunks_id ON chunks (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_chunks_chunk_id ON chunks (chunk_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_chunks_element_id ON chunks (element_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_chunks_document_id ON chunks (document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_chunks_content_hash ON chunks (content_hash)")

        conn.commit()
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
