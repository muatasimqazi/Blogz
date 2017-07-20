from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__, static_url_path='/static')

app.config['DEBUG'] = True
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://build-a-blog:password@localhost:8889/build-a-blog')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

app.secret_key = 'X68tVVWRUg5b^qd'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(20000))
    date = db.Column(db.DateTime)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner, date=None):
        self.title = title
        self.body = body
        self.owner = owner
        if date is None:
            date = datetime.utcnow()
        self.date = date

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.route('/newpost', methods=['GET', 'POST'])
def create_newpost():
    error_title = ''
    error_body = ''

    if request.method == 'POST':

        owner = User.query.filter_by(username=session['username']).first()
        blog_title = request.form['blog-title']
        if not blog_title:
            error_title = "Please fill in the title"
        elif len(blog_title) > 120:
            error_title = "Please take a shorter title"
        else:
            blog_body = request.form['blog-body']
            if not blog_body:
                error_body = 'Please fill in the body'

            elif len(blog_body) > 20000:
                error_body = 'Your blog post exceeds the limit'

            else:
                blog_post = Blog(blog_title, blog_body, owner)
                db.session.add(blog_post)
                db.session.commit()
                blog_id = blog_post.id;
                return redirect("/blog?id=" + str(blog_id))

    return render_template('new-post.html', error_title=error_title, error_body=error_body, title="New Blog Post")

@app.route('/blog', methods=['GET', 'POST'])
def display_posts():

    blog_id = request.args.get('id')
    if  blog_id:

        blog_post = Blog.query.filter_by(id=blog_id).first()
        return render_template('blog.html', blog=blog_post, blog_id=blog_id, title="Build a Blog")

    else:
        blog_posts = Blog.query.all()
        return render_template('blog.html', blogs=blog_posts, title="Build a Blog")


@app.before_request
def require_login():
    allowed_routes = ['index', 'display_posts', 'login', 'register']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/signup', methods=['POST', 'GET'])
def signup():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        if not username or not password or not verify:
            error = "One or more fields left blank"

        elif password != verify :
            error = "Passwords don't match"
        elif len(username) < 3:
            error = "Username too short"
        elif len(password) < 3:
            error = "Password too short"
        else:
            existing_user = User.query.filter_by(username=username).first()

            if not existing_user:
                new_user = User(username, password)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                return  redirect('/newpost')

            else:
                error = "Username already exists"
        return render_template('signup.html', error=error)

    return render_template('signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        username_error = ''
        password_error = ''
        if user:
            if user.password == password:
                session['username'] = username
                return redirect('/newpost')

            if user.password != password :
                password_error = 'Incorrect password'

        else:
            username_error = "This username does not exist"

        return render_template('login.html', username_error=username_error, password_error=password_error)

    return render_template('login.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')

@app.route('/')
def index():

    users = User.query.all()
    return render_template('index.html', users=users)

if __name__ == '__main__':
    app.run()
