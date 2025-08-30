from flask import Blueprint, request, redirect, url_for, session, flash, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from datetime import datetime

# This will be initialized in app.py
mysql = MySQL()
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO UsersProfile (FirstName, LastName, Username, Email, PhoneNumber, Password, CreatedAt)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, username, email, phone_number, hashed_password, datetime.now()))
        mysql.connection.commit()
        cur.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT UserID, FirstName, Password FROM UsersProfile WHERE Username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['firstname'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
