import sqlite3

conn = sqlite3.connect('database.db')
conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pin TEXT, role TEXT)')
conn.execute("INSERT OR IGNORE INTO users (name, email, pin, role) VALUES ('Test User', 'test@example.com', '1234', 'Content Creator')")
conn.commit()
conn.close()

print('Database setup complete with test user: test@example.com / 1234')
