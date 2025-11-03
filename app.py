from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_this_in_production'

# Database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Register page - GET request
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        pin = request.form['pin']
        role = request.form['role']
        
        conn = get_db_connection()
        
        # Check if email already exists
        existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if existing_user:
            conn.close()
            return render_template('register.html', error='Email already registered!')
        
        # Insert new user
        try:
            conn.execute('INSERT INTO users (name, email, pin, role) VALUES (?, ?, ?, ?)',
                        (name, email, pin, role))
            conn.commit()
            conn.close()
            
            # Store user info in session
            session['name'] = name
            session['email'] = email
            session['role'] = role
            
            return redirect(url_for('home'))
        except:
            conn.close()
            return render_template('register.html', error='Registration failed. Please try again.')
    
    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        pin = request.form['pin']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ? AND pin = ?', 
                           (email, pin)).fetchone()
        conn.close()
        
        if user:
            # Store user info in session
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid email or PIN')
    
    return render_template('login.html')

# Home/Dashboard page (after login)
@app.route('/home')
def home():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    return render_template('home.html', 
                         name=session.get('name'),
                         email=session.get('email'),
                         role=session.get('role'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

