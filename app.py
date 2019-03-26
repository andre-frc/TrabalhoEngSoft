from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from data import Articles
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import mysql.connector
from functools import wraps

app = Flask(__name__)

conn = mysql.connector.connect(user='lcarneiro', password='Carne1r0', host='localhost', database='MyFlaskApp', buffered=True)

Articles = Articles()

# Home page
@app.route('/')
def index():
    return render_template('home.html')

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

#Articles Page
@app.route('/articles')
def articles():
    return render_template('articles.html', articles = Articles)

# Single Article View
@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id=id)

# Class Register Form
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = conn.cursor(dictionary=True)

        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        conn.commit()

        # close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))
    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create cursor
        cur = conn.cursor(dictionary=True)

        # get user by username
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        result = cur.fetchone()

        if result:
            #get stored hash
            password = result['password']

            # compare pwds
            if sha256_crypt.verify(password_candidate, password):
                # correct password
                session['logged_in'] = True
                session['username'] = username

                flash ('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Incorrect password'
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

#Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap (*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')


if __name__ =='__main__':
    app.secret_key='secret123'
    app.run(debug=True)
