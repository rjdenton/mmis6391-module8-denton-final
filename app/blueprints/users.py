from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.db_connect import get_db

users = Blueprint('users', __name__)

@users.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']  # Capture the email field
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not email or not password:
            flash("Username, email, and password are required.", "danger")
            return redirect(url_for('users.register'))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('users.register'))

        connection = get_db()

        # Check if the email already exists
        query = "SELECT * FROM users WHERE email = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, (email,))
            user = cursor.fetchone()

        if user:
            flash("Email is already registered. Please use a different email.", "danger")
            return redirect(url_for('users.register'))

        # Check if the username already exists
        query = "SELECT * FROM users WHERE username = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, (username,))
            user = cursor.fetchone()

        if user:
            flash("Username is already taken. Please choose a different username.", "danger")
            return redirect(url_for('users.register'))

        # Insert the new user into the database
        hashed_password = generate_password_hash(password)
        query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
        with connection.cursor() as cursor:
            cursor.execute(query, (username, email, hashed_password))
        connection.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('users.login'))

    return render_template("register.html")

@users.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = get_db()
        query = "SELECT * FROM users WHERE username = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, (username,))
            user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login successful!", "success")
            return redirect(url_for('index'))  # Redirect to index (homepage)
        else:
            flash("Invalid credentials. Please try again.", "danger")

    return render_template("login.html")


@users.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('users.login'))

@users.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash("Please log in to view your profile.", "warning")
        return redirect(url_for('users.login'))

    connection = get_db()
    user_id = session['user_id']
    query = "SELECT * FROM users WHERE id = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

    # Handle profile update (POST request)
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        bio = request.form.get('bio')

        update_query = """
            UPDATE users 
            SET first_name = %s, last_name = %s, email = %s, bio = %s 
            WHERE id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(update_query, (first_name, last_name, email, bio, user_id))
        connection.commit()

        # Success message and reload in view mode
        return render_template("profile.html", user=user, editing=False, success_message="Profile updated successfully!")

    # Render profile in edit or view mode (GET request)
    editing = request.args.get('edit') == 'True'
    return render_template("profile.html", user=user, editing=editing)


