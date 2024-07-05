import sqlite3

def create_tables():
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            status TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect('chatbot.db')

def insert_sample_data():
    conn = get_connection()
    c = conn.cursor()

    sample_orders = [
        ('12345', 'Shipped'),
        ('67890', 'Processing'),
        ('54321', 'Delivered')
    ]
    c.executemany('INSERT OR REPLACE INTO orders (order_id, status) VALUES (?, ?)', sample_orders)

    sample_requests = [
        ('John Doe', 'john@example.com', '1234567890', 'open'),
        ('Jane Smith', 'jane@example.com', '0987654321', 'closed'),
        ('Alice Johnson', 'alice@example.com', '5551234567', 'open')
    ]
    c.executemany('INSERT INTO service_requests (name, email, phone, status) VALUES (?, ?, ?, ?)', sample_requests)

    conn.commit()
    conn.close()
