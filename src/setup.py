import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from database folder
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'database', '.env'))


def get_connection():
    """Establish and return a PostgreSQL database connection."""
    return psycopg2.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=os.getenv('DATABASE_PORT', '5432'),
        database=os.getenv('DATABASE_NAME', 'metreecs_db'),
        user=os.getenv('DATABASE_USER', 'postgres'),
        password=os.getenv('DATABASE_PASSWORD', '')
    )


def create_tables(conn):
    """Create the database tables if they don't exist."""
    cursor = conn.cursor()
    
    # Drop and recreate movements table to apply new schema
    cursor.execute("DROP TABLE IF EXISTS movements;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movements (
            id SERIAL PRIMARY KEY,
            product_id VARCHAR(50) NOT NULL,
            quantity INTEGER NOT NULL,
            type INTEGER NOT NULL CHECK (type IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_movements_product_id 
        ON movements(product_id, id DESC);
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            idempotency_key UUID NOT NULL PRIMARY KEY,
            response JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    conn.commit()
    cursor.close()
    print("Tables created successfully!")


def seed_data(conn):
    """Initialize the database with sample data."""
    cursor = conn.cursor()
    
    # Sample movements data
    sample_movements = [
        # Product ABC123: 100 in, 30 out = 70 stock
        ('ABC123', 100, 0),  # in
        ('ABC123', 30, 1),   # out
        
        # Product XYZ789: 200 in, 50 out, 25 out = 125 stock
        ('XYZ789', 200, 0),
        ('XYZ789', 50, 1),
        ('XYZ789', 25, 1),
        
        # Product DEF456: 75 in, 10 out = 65 stock
        ('DEF456', 75, 0),
        ('DEF456', 10, 1),
        
        # Product GHI321: 500 in, 150 out, 100 in = 450 stock
        ('GHI321', 500, 0),
        ('GHI321', 150, 1),
        ('GHI321', 100, 0),
    ]
    
    cursor.executemany(
        "INSERT INTO movements (product_id, quantity, type) VALUES (%s, %s, %s)",
        sample_movements
    )
    
    conn.commit()
    cursor.close()
    print(f"Seeded {len(sample_movements)} sample movements!")


def main():
    try:
        conn = get_connection()
        print("Successfully connected to PostgreSQL database!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        cursor.close()
        
        create_tables(conn)
        seed_data(conn)
        
        conn.close()
        print("Connection closed.")
        
    except Exception as e:
        print(f"Error connecting to database: {e}")


if __name__ == "__main__":
    main()
