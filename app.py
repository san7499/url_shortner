from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random
import string
import os

app = Flask(__name__)

# Generate random short code
def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Initialize database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

# Home page with form
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['original_url'].strip()

        if not original_url.startswith(('http://', 'https://')):
            original_url = 'http://' + original_url

        short_code = generate_short_code()

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # Ensure unique short code
        while True:
            c.execute("SELECT 1 FROM urls WHERE short_code = ?", (short_code,))
            if not c.fetchone():
                break
            short_code = generate_short_code()

        try:
            c.execute("INSERT INTO urls (original_url, short_code) VALUES (?, ?)", (original_url, short_code))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Error: Could not shorten URL", 500
        finally:
            conn.close()

        # Use deployed domain if available
        base_url = os.environ.get("BASE_URL", request.host_url)
        short_url = base_url.rstrip('/') + '/' + short_code

        return render_template('short_url.html', short_url=short_url)

    return render_template('index.html')

# Redirect from short URL
@app.route('/<short_code>')
def redirect_url(short_code):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT original_url FROM urls WHERE short_code = ?", (short_code,))
    result = c.fetchone()
    conn.close()

    if result:
        return redirect(result[0])
    else:
        return render_template('404.html'), 404

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
