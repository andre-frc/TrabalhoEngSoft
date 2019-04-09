from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import psycopg2
import psycopg2.extras
import psycopg2.extensions
from functools import wraps

app = Flask(__name__)

conn = psycopg2.connect("dbname='d5p6t7bcc56c7c' user='bqmmkvzngwjkws' host='ec2-54-221-201-212.compute-1.amazonaws.com' password='2681ee5e9edd27c58e5104b4c6f7ddd2bfb33d4de8d3a3fd1f793422e05d9615'")


# Home page
@app.route('/')
def index():
    return render_template('home.html')

# About Page
@app.route('/about')
def about():
    return render_template('about.html')

#Questions Page
@app.route('/questions')
def articles():
    return render_template('questions.html', articles = Null)

# Single Question View
@app.route('/question/<string:id>/')
def article(id):
    return render_template('question.html', id=id)

# Class Register Form
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    description = TextAreaField('Description', [validators.Length(min=30)])
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
        description = form.description.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create cursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("INSERT INTO user(name, description, login, password, isActive) VALUES(%s, %s, %s, %s, True)", (name, description, login, password))

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
                session['user_id'] = result['id']

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
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')

#Question add form
class QuestionForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=100)])
    description = TextAreaField('Description', [validators.Length(min=30)])

# Add Question
@app.route('/add_question', methods=['GET', 'POST'])
@is_logged_in
def addQuestion():
    form = QuestionForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        description = form.description.data

        #Create cursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("INSERT INTO question(title, description, user_id) VALUES(%s, %s, %s)", (name, description, session['id']))

        # Commit to DB
        conn.commit()

        # close connection
        cur.close()

        flash('Question Created!', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_question.html', form = form)

if __name__ =='__main__':
    app.secret_key='secret123'
    app.run(debug=True)
