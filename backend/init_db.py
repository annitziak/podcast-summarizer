# init_db.py
import sqlite3

def init_db(db_path="podcast.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create episodes table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS episodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        audio_url TEXT,
        duration INTEGER, -- in seconds
        status TEXT DEFAULT 'queued', -- queued, processing, done
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create transcripts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transcripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        episode_id INTEGER NOT NULL,
        text TEXT, -- full transcript
        segments_json TEXT, -- JSON string [{start, end, text}]
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (episode_id) REFERENCES episodes(id)
    );
    """)

    # Create summaries table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        episode_id INTEGER NOT NULL,
        summary_text TEXT,
        chapters_json TEXT, -- JSON string [{timestamp, title}]
        quotes_json TEXT,   -- JSON string of key quotes
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (episode_id) REFERENCES episodes(id)
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
