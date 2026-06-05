import os
import sqlite3

try:
    import psycopg2
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

class SQLiteCursorWrapper:
    """Wraps an SQLite cursor to emulate PostgreSQL syntax (translating %s placeholders to ?)."""
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        # Adapt PostgreSQL query to SQLite
        query = query.replace("%s", "?")
        query = query.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        query = query.replace("TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        query = query.replace("NUMERIC", "REAL")
        
        if params is not None:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def close(self):
        self.cursor.close()

class SQLiteConnectionWrapper:
    """Wraps an SQLite connection to emulate standard DB-API behavior and handle cursor mapping."""
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()

def get_connection():
    """
    Attempts to connect to PostgreSQL using environment variables.
    Falls back to SQLite if PostgreSQL credentials are not configured or unavailable.
    """
    db_type = "PostgreSQL"

    # Read credentials from environment variables (never hardcode secrets)
    database_url = os.environ.get("DATABASE_URL")          # Render sets this automatically
    db_host      = os.environ.get("DB_HOST")
    db_name      = os.environ.get("DB_NAME")
    db_user      = os.environ.get("DB_USER")
    db_pass      = os.environ.get("DB_PASS")

    try:
        if not HAS_PSYCOPG2:
            raise ImportError("psycopg2 module is not available or failed to load.")
        if database_url:
            # Render / Heroku style: postgres://user:pass@host/db
            conn = psycopg2.connect(database_url, connect_timeout=3, sslmode="require")
        elif db_host and db_name and db_user and db_pass:
            conn = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_pass,
                connect_timeout=3,
            )
        else:
            raise EnvironmentError("No PostgreSQL credentials found in environment.")
        return conn, db_type
    except Exception as e:
        print(f"[Warning] PostgreSQL connection failed: {e}. Falling back to SQLite.")
        db_type = "SQLite"

        # Ensure database directory exists
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        db_dir = os.path.join(base_dir, "database")
        os.makedirs(db_dir, exist_ok=True)
        sqlite_path = os.path.join(db_dir, "credit_risk.db")
        conn = sqlite3.connect(sqlite_path)
        return SQLiteConnectionWrapper(conn), db_type

def init_db():
    """
    Initializes the database tables if they do not exist.
    """
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    print(f"Initializing predictions table on {db_type}...")
    
    # Create predictions table
    # We include fields to store both input features and prediction results for tracking & auditable logs.
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            loan_id VARCHAR(100),
            annual_income NUMERIC,
            credit_score INT,
            loan_amount NUMERIC,
            employment_status VARCHAR(50),
            education_level VARCHAR(50),
            existing_debt NUMERIC,
            approval_status VARCHAR(50),
            risk_score NUMERIC,
            model_version VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    cursor.close()
    conn.close()
    print("Database initialization completed successfully!")

if __name__ == "__main__":
    init_db()
