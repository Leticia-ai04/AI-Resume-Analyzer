import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from ml_utils import analyze_resume, extract_text, generate_pdf_report, init_db
from io import BytesIO
import sqlite3
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATABASE = 'users.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_user_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_user_db()

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        if not (username and email and password and confirm_password):
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            conn = get_db()
            c = conn.cursor()
            # Check if username or email exists
            c.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
            if c.fetchone():
                error = "Username or Email already registered."
            else:
                hashed_pw = generate_password_hash(password)
                c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_pw))
                conn.commit()
                conn.close()
                flash("Registration successful! Please login.", "success")
                return redirect(url_for('login'))
            conn.close()
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not (username and password):
            error = "Please enter username and password."
        else:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            conn.close()
            if user and check_password_hash(user['password'], password):
                session['user'] = username
                flash(f"Welcome back, {username}!", "success")
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid credentials."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    analysis_result = None
    error = None

    if request.method == 'POST':
        # Handle file upload or job description paste
        uploaded_file = request.files.get('resume_file')
        job_description = request.form.get('job_description', '').strip()

        if uploaded_file and uploaded_file.filename != '':
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4().hex}_{filename}")
            uploaded_file.save(filepath)
            try:
                resume_text = extract_text(filepath)
            except Exception as e:
                error = f"Error extracting text from file: {str(e)}"
                resume_text = ''
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            error = "Please upload a resume file."

        if not error and resume_text:
            try:
                analysis_result = analyze_resume(resume_text, job_description)
                session['last_analysis'] = analysis_result
            except Exception as e:
                error = f"Error analyzing resume: {str(e)}"

    return render_template('dashboard.html', username=session['user'], analysis=analysis_result, error=error)

@app.route('/download_pdf')
def download_pdf():
    if 'last_analysis' not in session:
        flash("Please perform a resume analysis first.", "warning")
        return redirect(url_for('dashboard'))

    analysis = session['last_analysis']
    pdf_io = BytesIO()
    generate_pdf_report(analysis, pdf_io)
    pdf_io.seek(0)

    return send_file(pdf_io,
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name='Resume_Analysis_Report.pdf')

if __name__ == "__main__":
    app.run(debug=True)
