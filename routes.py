from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify, make_response, send_file,jsonify 
from app import app
from models import db, User, Subject, Chapter, Quiz, Questions, Scores
from datetime import datetime,timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from flask import send_file




## Decorators

def auth_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('please login to continue')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return inner

def admin_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('please login to continue')
            return redirect(url_for('login'))
        user=User.query.get(session['user_id'])
        if user.is_admin!=True:
            flash('You are not authorized to view this page')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return inner

## Index page routes 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')           
def login():
    return render_template('auth/login.html') 

@app.route('/login', methods=['POST'])
def login_post():
    username=request.form.get('username')
    password=request.form.get('password')
    
    if username=='' or password=='':
        flash('Username and password cannot be empty')

    user=User.query.filter_by(username=username).first()
    
    if not user:
        flash('User details not found')
        return redirect(url_for('login'))
    
    elif not user.check_password(password):
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    #if login successful
    session['user_id']=user.id
    #session['username']=user.username
    flash('Login successful')
    if user.is_admin==True:
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    #session.pop('username', None)
    flash('Logout successful')
    return redirect(url_for('login'))


@app.route('/register')
def register():
    return render_template('auth/register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username=request.form.get('username')
    password=request.form.get('password')
    name=request.form.get('name')
    qualification=request.form.get('qualification')
    
    user=User.query.filter_by(username=username).first()
    if user:
        flash('User already exists')
        return redirect(url_for('register'))
    
    new_user=User(username=username, passhash=generate_password_hash(password), name=name, qualification=qualification)
    db.session.add(new_user)
    db.session.commit()
    
    flash('Registration successful. Please Log In')
    return redirect(url_for('login'))

## user / student routes 

@app.route('/profile')
@auth_required 
def profile():
    user=User.query.get(session['user_id'])
    return render_template('student/profile.html',user=user)

@app.route('/profile', methods=['POST'])
@auth_required
def profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')
    qualification = request.form.get('qualification')

    if not username or not cpassword or not password :
        flash('Please fill out all the required fields')
        return redirect(url_for('profile'))
    
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('profile'))
    
    if username != user.username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('profile'))
    
    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    user.qualification = qualification
        
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))

@app.route('/scores')
@auth_required
def scores():
    return render_template('scores.html') 

@app.route("/summary")
@auth_required
def summary():
    return render_template('summary.html')

## Admin routes 

@app.route('/admin/dashboard')
@admin_required
@auth_required
def admin_dashboard():
    return render_template('/admin/admin_dashboard.html')

## profile routes for admin
'''
@app.route('/admin/profile')
@admin_required
def admin_profile():
    user=User.query.get(session['user_id'])
    return render_template('admin/admin_profile.html',user=user)

@app.route('/admin/profile', methods=['POST'])
@auth_required
def admin_profile_post():
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    
    if not cpassword or not password :
        flash('Please fill out all the required fields')
        return redirect(url_for('admin_profile'))
    
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('admin_profile'))
    
    new_password_hash = generate_password_hash(password)
    user.passhash = new_password_hash

    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('admin_profile'))

'''

@app.route("/admin/summary")
@admin_required
def admin_summary():
    return render_template('admin/admin_summary.html')

@app.route("/admin/manage_quiz")
@admin_required
def manage_quiz():
    return render_template('admin/manage_quiz.html')


