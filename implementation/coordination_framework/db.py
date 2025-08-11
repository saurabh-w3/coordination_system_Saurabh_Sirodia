import sqlite3, os, threading

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'demonstration', 'state.sqlite')
_database_lock = threading.Lock()

SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS applications (
      app_id TEXT,
      field TEXT,
      value TEXT,
      PRIMARY KEY (app_id, field)
    )""",

    """CREATE TABLE IF NOT EXISTS verifications (
      app_id TEXT,
      proof TEXT,
      value TEXT,
      PRIMARY KEY (app_id, proof)
    )""",

    """CREATE TABLE IF NOT EXISTS emi (
      app_id TEXT PRIMARY KEY,
      amount REAL
    )""",

    """CREATE TABLE IF NOT EXISTS eligibility (
      app_id TEXT PRIMARY KEY,
      status TEXT,
      confidence REAL
    )""",

    """CREATE TABLE IF NOT EXISTS leads (
      app_id TEXT,
      bank TEXT,
      status TEXT,
      meta TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    """CREATE TABLE IF NOT EXISTS events (
      ts REAL,
      agent TEXT,
      metric TEXT,
      value TEXT,
      extra TEXT
    )"""
]

def get_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    try:
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=WAL;')
        return conn
    except Exception:
        # Fallback: in-memory DB if disk is unavailable
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        return conn

def initialize_database():
    conn = get_connection()
    try:
        with conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)
    except Exception:
        pass
    return conn

def write_event(conn, timestamp, agent, metric, value, extra=''):
    try:
        with _database_lock, conn:
            conn.execute('INSERT INTO events(ts,agent,metric,value,extra) VALUES (?,?,?,?,?)',
                         (timestamp, agent, metric, str(value), extra))
    except Exception:
        # swallow and continue; logging should not crash system
        pass

def get_fields(conn, app_id):
    try:
        cur = conn.execute('SELECT field, value FROM applications WHERE app_id=?', (app_id,))
        return {k: v for k, v in cur.fetchall()}
    except Exception:
        return {}

def set_field(conn, app_id, field, value):
    with _database_lock, conn:
        conn.execute('INSERT OR REPLACE INTO applications(app_id,field,value) VALUES (?,?,?)', (app_id, field, str(value)))

def set_proof(conn, app_id, proof, value):
    with _database_lock, conn:
        conn.execute('INSERT OR REPLACE INTO verifications(app_id,proof,value) VALUES (?,?,?)', (app_id, proof, str(value)))

def get_proofs(conn, app_id):
    try:
        cur = conn.execute('SELECT proof, value FROM verifications WHERE app_id=?', (app_id,))
        return {k: v for k, v in cur.fetchall()}
    except Exception:
        return {}

def set_emi(conn, app_id, amount):
    with _database_lock, conn:
        conn.execute('INSERT OR REPLACE INTO emi(app_id,amount) VALUES (?,?)', (app_id, float(amount)))

def get_emi(conn, app_id):
    try:
        cur = conn.execute('SELECT amount FROM emi WHERE app_id=?', (app_id,))
        row = cur.fetchone()
        return float(row[0]) if row else None
    except Exception:
        return None

def set_eligibility(conn, app_id, status, confidence):
    with _database_lock, conn:
        conn.execute('INSERT OR REPLACE INTO eligibility(app_id,status,confidence) VALUES (?,?,?)',
                     (app_id, status, float(confidence)))

def get_eligibility(conn, app_id):
    try:
        cur = conn.execute('SELECT status, confidence FROM eligibility WHERE app_id=?', (app_id,))
        row = cur.fetchone()
        return (row[0], float(row[1])) if row else (None, None)
    except Exception:
        return (None, None)

def add_lead(conn, app_id, bank, status, meta):
    with _database_lock, conn:
        conn.execute('INSERT INTO leads(app_id,bank,status,meta) VALUES (?,?,?,?)', (app_id, bank, status, meta))
