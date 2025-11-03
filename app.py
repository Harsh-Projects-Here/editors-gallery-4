import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_this_in_production'

# --- Database Setup (Vercel-compatible) ---
DB_PATH = '/tmp/database.db'  # only /tmp is writable on Vercel

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Create database and one test user if not exists
if not os.path.exists(DB_PATH):
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        pin TEXT NOT NULL,
                        role TEXT NOT NULL
                    )''')
    conn.execute("INSERT INTO users (name, email, pin, role) VALUES (?, ?, ?, ?)",
                 ("Test User", "test@example.com", "1234", "Content Creator"))
    conn.commit()
    conn.close()
    print("✅ Database initialized with test user.")

# --- Routes ---

@app.route('/')
def home():
    return "<h1>Welcome to Editors Gallery</h1><p><a href='/login'>Login</a> or <a href='/register'>Register</a></p>"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        pin = request.form['pin']
        role = request.form['role']

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (name, email, pin, role) VALUES (?, ?, ?, ?)",
                         (name, email, pin, role))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
        except sqlite3.IntegrityError:
            flash('This email is already registered. Try another.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('login'))

    return '''
        <h2>Register</h2>
        <form method="post">
            Name: <input type="text" name="name" required><br>
            Email: <input type="email" name="email" required><br>
            PIN: <input type="password" name="pin" required><br>
            Role:
            <select name="role" required>
                <option value="Video Editor">Video Editor</option>
                <option value="Content Creator">Content Creator</option>
            </select><br>
            <button type="submit">Register</button>
        </form>
        <p><a href='/login'>Already have an account? Login</a></p>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pin = request.form['pin']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND pin = ?", (email, pin)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['name'] = user['name']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or PIN.', 'danger')
            return redirect(url_for('login'))

    return '''
        <h2>Login</h2>
        <form method="post">
            Email: <input type="email" name="email" required><br>
            PIN: <input type="password" name="pin" required><br>
            <button type="submit">Login</button>
        </form>
        <p><a href='/register'>Create a new account</a></p>
    '''

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return f"<h2>Welcome, {session['name']}!</h2><p>You are logged in successfully.</p><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Run the app locally ---
if __name__ == '__main__':
    app.run(debug=True)
