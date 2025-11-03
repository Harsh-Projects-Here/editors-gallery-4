import os
import sqlite3
import logging
import traceback
from flask import Flask, render_template, request, redirect, url_for, session

# --- Flask setup ---
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_in_production")

# configure logging to stdout (Vercel captures stdout)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(handler)

# --- Database helpers ---
DB_FILENAME = "database.db"
DB_PATH = os.path.join(app.root_path, DB_FILENAME)

def ensure_db():
    """Create database file and users table if they don't exist."""
    if not os.path.exists(DB_PATH):
        app.logger.info(f"Creating database at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            pin TEXT,
            role TEXT
        )
    ''')
    # optional test user (won't create duplicate because of UNIQUE + INSERT OR IGNORE)
    conn.execute(
        "INSERT OR IGNORE INTO users (name, email, pin, role) VALUES (?, ?, ?, ?)",
        ("Test User", "test@example.com", "1234", "Content Creator")
    )
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Ensure DB exists at startup
ensure_db()

# --- Routes ---
@app.route("/")
def index():
    try:
        return render_template("index.html")
    except Exception:
        app.logger.exception("Exception in index route")
        # re-raise so error handler / logs capture it
        raise

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        pin = request.form.get("pin", "").strip()
        role = request.form.get("role", "").strip()

        if not (name and email and pin and role):
            return render_template("register.html", error="Please fill all fields.")

        try:
            conn = get_db_connection()
            existing_user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if existing_user:
                conn.close()
                return render_template("register.html", error="Email already registered!")

            conn.execute(
                "INSERT INTO users (name, email, pin, role) VALUES (?, ?, ?, ?)",
                (name, email, pin, role)
            )
            conn.commit()
            conn.close()

            session["name"] = name
            session["email"] = email
            session["role"] = role
            return redirect(url_for("home"))
        except Exception:
            app.logger.exception("Exception in register")
            return render_template("register.html", error="Registration failed. Please try again.")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        pin = request.form.get("pin", "").strip()
        try:
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE email = ? AND pin = ?", (email, pin)).fetchone()
            conn.close()
            if user:
                session["name"] = user["name"]
                session["email"] = user["email"]
                session["role"] = user["role"]
                return redirect(url_for("home"))
            else:
                return render_template("login.html", error="Invalid email or PIN")
        except Exception:
            app.logger.exception("Exception in login")
            return render_template("login.html", error="Login failed. Please try again.")
    return render_template("login.html")

@app.route("/home")
def home():
    if "email" not in session:
        return redirect(url_for("login"))
    return render_template("home.html",
                           name=session.get("name"),
                           email=session.get("email"),
                           role=session.get("role"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- Error handler to log stack traces ---
@app.errorhandler(500)
def internal_error(err):
    tb = traceback.format_exc()
    app.logger.error("Internal Server Error: %s\nTraceback:\n%s", err, tb)
    # Return a friendly message (still 500). Avoid returning traceback to public.
    return "Internal Server Error", 500

# Only for local testing. Vercel uses the module entrypoint instead.
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

