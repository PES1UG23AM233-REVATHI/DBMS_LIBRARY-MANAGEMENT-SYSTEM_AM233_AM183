# db.py
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Force reload of .env file
load_dotenv(override=True)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "library_management_db"),  # ✅ match schema name
    "autocommit": False
}

def get_conn():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

def query(sql, params=None, fetch=False):
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())
    if fetch:
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    else:
        conn.commit()
        cursor.close()
        conn.close()
        return None


# ✅ NEW helper: Call stored procedures (e.g., ProcessReturn)
def call_procedure(proc_name, params=()):
    """
    Calls a stored procedure and returns any fetched results if present.
    Example: call_procedure('ProcessReturn', ('I001', '2025-10-20', 'Returned in good condition'))
    """
    conn = get_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.callproc(proc_name, params)
    
    results = []
    for result in cursor.stored_results():
        results.extend(result.fetchall())

    conn.commit()
    cursor.close()
    conn.close()
    return results
