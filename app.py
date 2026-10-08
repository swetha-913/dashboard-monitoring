import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, jsonify

try:
    import mysql.connector
except ImportError:
    mysql = None

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cyberguard_secret_key_production_2026")

API_KEY = os.environ.get("API_KEY", "cyberguard123")

failed_attempts = {}

# Database Configuration (supports Cloud MySQL or zero-config SQLite on Render)
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "cybersecurity_db")
default_db_dir = "/tmp" if os.path.isdir("/tmp") else os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.environ.get("DB_FILE", os.path.join(default_db_dir, "cybersecurity.db"))
class SQLiteCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=None):
        sqlite_query = query.replace("%s", "?")
        if params is None:
            return self._cursor.execute(sqlite_query)
        return self._cursor.execute(sqlite_query, params)

    def fetchall(self):
        return [dict(r) for r in self._cursor.fetchall()]

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row else None

    def close(self):
        self._cursor.close()

class SQLiteConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self, dictionary=False):
        return SQLiteCursorWrapper(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def close(self):
        return self._conn.close()

def get_db_connection():
    if DB_HOST and mysql:
        try:
            return mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT,
                connect_timeout=5
            )
        except Exception as e:
            print(f"[CyberGuard Warning] External MySQL connection failed ({e}). Falling back to SQLite.")

    # SQLite zero-configuration fallback for cloud environments like Render
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return SQLiteConnectionWrapper(conn)

def init_db():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        is_sqlite = isinstance(db, SQLiteConnectionWrapper)

        if is_sqlite:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    threat_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS threats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    threat_type VARCHAR(255) NOT NULL,
                    severity VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    description TEXT NOT NULL,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        db.commit()

        # Seed sample threat events if table is empty
        cursor.execute("SELECT COUNT(*) as cnt FROM threats")
        row = cursor.fetchone()
        count = row["cnt"] if isinstance(row, dict) else (row[0] if row else 0)

        if count == 0:
            sample_threats = [
                ("DDoS Attack", "Critical", "Open", "Volumetric 120 Gbps UDP flood targeting primary edge gateway cluster"),
                ("SQL Injection Probe", "Critical", "Investigating", "Malicious SQL payload injected into auth parameters: ' OR 1=1 --"),
                ("Brute Force Attack", "High", "Open", "Over 240 failed SSH authentication attempts detected from IP 194.26.29.112"),
                ("Ransomware Signature", "Critical", "Open", "Suspicious bulk file encryption heuristic flagged on internal NAS share"),
                ("Phishing Campaign", "Medium", "Resolved", "Spear-phishing email containing malicious PDF attachment quarantined"),
                ("Port Scanning Activity", "Low", "Resolved", "Reconnaissance TCP SYN scan detected across perimeter ports 21, 22, 8080")
            ]
            for item in sample_threats:
                cursor.execute(
                    "INSERT INTO threats (threat_type, severity, status, description) VALUES (%s, %s, %s, %s)",
                    item
                )
            db.commit()

        cursor.close()
        db.close()
    except Exception as e:
        print(f"[CyberGuard Warning] Database initialization: {e}")

# Initialize schema on startup
try:
    init_db()
except Exception as e:
    print(f"[CyberGuard] Startup DB init skipped: {e}")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        attempts = failed_attempts.get(username, 0)

        if username == "admin" and password == "admin123":
            session["logged_in"] = True
            failed_attempts[username] = 0
            return redirect("/")
        else:
            failed_attempts[username] = attempts + 1

            if failed_attempts[username] >= 5:
                db = get_db_connection()
                cursor = db.cursor()

                cursor.execute(
                    """
                    INSERT INTO threats
                    (threat_type, severity, status, description)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        "Brute Force Attack",
                        "Critical",
                        "Open",
                        f"Multiple failed login attempts ({failed_attempts[username]}) detected for user: {username}"
                    )
                )

                db.commit()
                cursor.close()
                db.close()

                return render_template(
                    "login.html",
                    error="🚨 Brute Force Attack Detected! Multiple failed login attempts logged to security dashboard."
                )

            return render_template(
                "login.html",
                error=f"Invalid username or password. Attempt {failed_attempts[username]} of 5."
            )

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/login")

@app.route("/")
def dashboard():
    if not session.get("logged_in"):
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM threats ORDER BY detected_at DESC")
    threats = cursor.fetchall()

    cursor.close()
    db.close()

    total = len(threats)
    critical = sum(1 for t in threats if t["severity"] == "Critical")
    open_threats = sum(1 for t in threats if t["status"] == "Open")
    resolved = sum(1 for t in threats if t["status"] == "Resolved")

    latest_alert = None
    if threats and threats[0]["severity"] == "Critical":
        latest_alert = threats[0]

    return render_template(
        "dashboard.html",
        threats=threats,
        total=total,
        critical=critical,
        open_threats=open_threats,
        resolved=resolved,
        latest_alert=latest_alert
    )

@app.route("/add-threat", methods=["GET", "POST"])
def add_threat():
    if not session.get("logged_in"):
        return redirect("/login")

    if request.method == "POST":
        threat_type = request.form.get("threat_type", "").strip()
        severity = request.form.get("severity", "Medium")
        status = request.form.get("status", "Open")
        description = request.form.get("description", "").strip()

        db = get_db_connection()
        cursor = db.cursor()

        query = """
        INSERT INTO threats
        (threat_type, severity, status, description)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (threat_type, severity, status, description)
        )

        db.commit()
        cursor.close()
        db.close()

        return redirect("/")

    return render_template("add_threat.html")

@app.route("/delete-threat/<int:threat_id>")
def delete_threat(threat_id):
    if not session.get("logged_in"):
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM threats WHERE id = %s",
        (threat_id,)
    )

    db.commit()
    cursor.close()
    db.close()

    return redirect("/")

@app.route("/edit-threat/<int:threat_id>", methods=["GET", "POST"])
def edit_threat(threat_id):
    if not session.get("logged_in"):
        return redirect("/login")

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        threat_type = request.form.get("threat_type", "").strip()
        severity = request.form.get("severity", "Medium")
        status = request.form.get("status", "Open")
        description = request.form.get("description", "").strip()

        cursor.execute(
            """
            UPDATE threats
            SET threat_type=%s,
                severity=%s,
                status=%s,
                description=%s
            WHERE id=%s
            """,
            (
                threat_type,
                severity,
                status,
                description,
                threat_id
            )
        )

        db.commit()
        cursor.close()
        db.close()

        return redirect("/")

    cursor.execute(
        "SELECT * FROM threats WHERE id = %s",
        (threat_id,)
    )

    threat = cursor.fetchone()
    cursor.close()
    db.close()

    if not threat:
        return redirect("/")

    return render_template(
        "edit_threat.html",
        threat=threat
    )

@app.route("/api/report-threat", methods=["POST"])
def report_threat():
    if request.headers.get("X-API-Key") != API_KEY:
        return {
            "error": "Unauthorized API request"
        }, 401

    data = request.get_json(silent=True) or {}

    threat_type = data.get("threat_type")
    severity = data.get("severity", "Medium")
    description = data.get("description", "")

    if not threat_type or not description:
        return {"error": "threat_type and description are required"}, 400

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO threats
        (threat_type, severity, status, description)
        VALUES (%s, %s, %s, %s)
        """,
        (
            threat_type,
            severity,
            "Open",
            description
        )
    )

    db.commit()
    cursor.close()
    db.close()

    return {
        "message": "Threat reported successfully",
        "threat_type": threat_type,
        "severity": severity
    }

@app.route("/healthz")
def healthz():
    return {"status": "ok", "service": "CyberGuard Dashboard"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)