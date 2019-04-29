from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
import psycopg2
import psycopg2.extras
import psycopg2.extensions
from functools import wraps
from datetime import datetime


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
def questions():
    
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("SELECT id, title FROM public.question WHERE \"isActive\"=%s LIMIT 20", (bool(1),))

    questions = cur.fetchall()
    print (questions)

    conn.commit()

    cur.close()

    return render_template('questions.html', questions = questions)

#Response add form
class ResponseForm(Form):
    description = TextAreaField('',[validators.Length(min=30)])

# Single Question View
@app.route('/question/<string:id>/', methods=['GET','POST'])
def question(id):

    form = ResponseForm(request.form)
    if request.method == 'POST' and form.validate():
        comment = form.description.data

        # create cursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("INSERT INTO public.answer (comment, user_id, question_id, \"isActive\") VALUES (%s, %s, %s, %s)", (comment, session['user_id'], id, bool(1)))

        # Commit to DB
        conn.commit()

        # close connection
        cur.close()

        return redirect(url_for('question', id = id))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("SELECT q.id, q.title, q.description, q.\"createdAt\", u.name FROM public.question q JOIN public.user u ON q.user_id = u.id WHERE q.id = %s", (id))
    
    quest = cur.fetchone()

    conn.commit()

    cur.close()

    quest["createdAt"] = quest["createdAt"].strftime("%x")

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("SELECT * FROM public.answer a JOIN public.user u ON a.user_id = u.id WHERE a.question_id = %s and a.\"isActive\" = %s",(int(id), bool(1)))

    answers = cur.fetchall()

    for item in answers:
        item["createdAt"] = item["createdAt"].strftime("%x")

    # Commit to DB
    conn.commit()

    # close connection
    cur.close()

    return render_template('question.html', question=quest, form=form, answers=answers)

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

        cur.execute("INSERT INTO public.user (name, description, login, password, \"isActive\") VALUES (%s, %s, %s, %s, %s)", (name, description, username, password, bool(1)))

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
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # get user by username
        cur.execute("SELECT * FROM public.user WHERE login = %s", [username])
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
                session['name']=result['name']

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

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("SELECT id, title, description, \"createdAt\" FROM public.question  WHERE user_id = %s and \"isActive\"=%s ORDER BY id ASC", (session['user_id'],bool(1)))
    
    user_questions = cur.fetchall()

    
    if len(user_questions) > 0:
        for item in user_questions:
            item['createdAt']= item["createdAt"].strftime("%x")

        return render_template('dashboard.html', questions = user_questions)
    else:
        msg = "Você ainda não possui nenhuma questão"
        return render_template('dashboard.html', msg = msg)
    cur.close()

#Question add form
class QuestionForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=100)])
    description = TextAreaField('Description', [validators.Length(min=30, max=1000)])

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

        cur.execute("INSERT INTO public.question (title, description, user_id, \"isActive\") VALUES(%s, %s, %s, %s)", (title, description, session['user_id'], bool(1)))

        # Commit to DB
        conn.commit()

        # close connection
        cur.close()

        flash('Question Created!', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_question.html', form = form)

# Edit Question
@app.route('/edit_question/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def editQuestion(id):

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("SELECT q.id, q.title, q.description, q.\"createdAt\", u.name FROM public.question q JOIN public.user u ON q.user_id = u.id WHERE q.id = %s and q.\"isActive\"=%s", (id, bool(1)))
    
    question = cur.fetchone()

    conn.commit()

    cur.close()

    question["createdAt"] = question["createdAt"].strftime("%x")

    # get form
    form = QuestionForm(request.form)

    # populate for fields
    form.title.data = question["title"]
    form.description.data = question["description"]

    if request.method == 'POST' and form.validate():
        title = request.form["title"]
        description = request.form["description"]

        #Create cursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("UPDATE public.question SET title=%s, description=%s WHERE id=%s", (title, description, id))

        # Commit to DB
        conn.commit()

        # close connection
        cur.close()

        flash('Question Updated!', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_question.html', form = form)

# Delete Question
@app.route('/delete_question/<string:id>', methods=['DELETE', 'POST'])
@is_logged_in
def deleteQuestion(id):
    
    # Create cursor
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cur.execute("UPDATE public.question SET \"isActive\"=%s WHERE id=%s", (bool(0), id))

    conn.commit()

    cur.close()
    
    flash('Question deleted!', 'success')

    return redirect(url_for('dashboard'))

if __name__ =='__main__':
    app.secret_key='secret123'
    app.run(debug=True)
