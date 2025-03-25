from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify, make_response, send_file,jsonify 
from app import app
from models import db, User, Subject, Chapter, Quiz, Questions, Scores,Category
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
    
    if user.flagged==True:
        flash('This account has been banned temporarily, contact admin')
        return redirect(url_for('login'))
    
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
    confirm_password=request.form.get('confirm_password')
    name=request.form.get('name')
    qualification=request.form.get('qualification')
    
    user=User.query.filter_by(username=username).first()
    if user:
        flash('User already exists')
        return redirect(url_for('register'))
    
    if not username or not password or not confirm_password:
        flash('Please fill out all the required fields')
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
    # Fetch all subjects and their chapters
    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    #update question count for each chapter
    for chapter in chapters:
        question_count = Questions.query.filter(Questions.chapter_id == chapter.id).count()
        chapter.no_of_questions = question_count
    db.session.commit()

    if not subjects:
        flash('No subjects found, click + to add subjects')
    return render_template('/admin/admin_dashboard.html', subjects=subjects, chapters=chapters)

## Subject Description page 
@app.route('/admin/subjects')
@admin_required
@auth_required
def subject():
    # Fetch all subjects
    subjects = Subject.query.all()
    return render_template('admin/subjects.html', subjects=subjects)


## Add subjects 
@app.route('/admin/manage_subject')
@admin_required
def add_subject():
    usage='add'
    return render_template('admin/manage_subject.html', usage='add')

@app.route('/admin/manage_subject', methods=['POST'])
@admin_required
def add_subject_post():
    name=request.form.get('subject_name')
    description=request.form.get('description')
    category= request.form.get('category')

    if not name:
        flash('Subject name cannot be empty')
        return redirect(url_for('add_subject'))
    usage='add'
    subject=Subject.query.filter_by(name=name).first()
    if subject:
        flash('Subject already exists')
        return redirect(url_for('add_subject'))
    
    new_subject=Subject(name=name, Description=description, category=category)
    db.session.add(new_subject)
    db.session.commit()

    flash('Subject added successfully')

    return redirect(url_for('admin_dashboard'))

## Edit Subjects 
@app.route('/admin/manage_subject/<int:subject_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    usage = 'edit'
    if request.method == 'POST':
        subject.name = request.form.get('name')
        subject.Description = request.form.get('description')

        if subject.name=='' or subject.Description=='':
            flash('Please fill out all fields')
            return redirect(url_for('edit_subject', subject_id=subject_id))

        db.session.commit()
        flash('Subject updated successfully')
        return redirect(url_for('subject'))

    return render_template('admin/manage_subject.html', subject=subject, usage='edit')

## Delete Subjects
@app.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
@admin_required
@auth_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    chapter = Chapter.query.filter_by(subject_id=subject_id).all()
    quiz = Quiz.query.filter_by(subject_id=subject_id).all()
    for q in quiz:
        question = Questions.query.filter_by(quiz_id=q.id).all()
        for ques in question:
            db.session.delete(ques)
        db.session.delete(q)
    for chap in chapter:
        db.session.delete(chap)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully')
    return redirect(url_for('admin_dashboard'))

### manage chapters
@app.route('/admin/manage_chapter/<int:subject_id>', methods=['GET','POST'])
@admin_required
@auth_required
def add_chapter(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    usage = "add"
    if request.method == 'POST':
        chapter_name = request.form.get('chapter_name')
        description = request.form.get('description')

        if not chapter_name :
            flash('Please fill out all fields')
            return redirect(url_for('add_chapter', subject_id=subject_id , usage='add'))

        # Add the new chapter to the database
        new_chapter = Chapter(name=chapter_name, Description=description, subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()
        flash('Chapter added successfully')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/manage_chapter.html', subject_id=subject_id , subject=subject, usage='add')

#edit chapter
@app.route('/manage_chapter/<int:chapter_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    usage = 'edit'
    if request.method == 'POST':
        chapter.name = request.form.get('chapter_name')
        chapter.Description = request.form.get('description')

        if not chapter.name :
            flash('Please fill out all fields')
            return redirect(url_for('edit_chapter', chapter_id=chapter_id, usage='edit'))

        db.session.commit()
        flash('Chapter updated successfully')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/manage_chapter.html', chapter=chapter, usage='edit')

@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
@admin_required
@auth_required
def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully')
    return redirect(url_for('admin_dashboard'))

## quiz dashboard
@app.route('/admin/quiz')
@admin_required
@auth_required
def quiz_dashboard():
    # Fetch all subjects and their chapters
    quizzes = Quiz.query.all()
    questions = Questions.query.all()
    # Update the question count for each quiz

    for quiz in quizzes:
        question_count = Questions.query.filter(Questions.quiz_id == quiz.id).count()
        quiz.no_of_questions = question_count
    db.session.commit()  # Commit the updates to the database

    if not quizzes:
        flash('No quizzes found, click + to add quizzes')
    return render_template('/admin/quiz.html', quizzes=quizzes,questions=questions)

## Add Quiz
@app.route('/admin/manage_quiz/add/<int:chapter_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def add_quiz(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    usage = 'add'

    if request.method == 'POST':
        name = request.form.get('quiz_name')
        description = request.form.get('description')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        time_duration = request.form.get('time_duration')
        is_active = request.form.get('is_active')
        # Convert start_date and end_date to Python date objects
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        except ValueError:
            flash('Invalid start date format. Please use YYYY-MM-DD.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            flash('Invalid end date format. Please use YYYY-MM-DD.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        # Convert time_duration to Python time object
        try:
            time_duration = datetime.strptime(time_duration, '%H:%M').time() if time_duration else None
        except ValueError:
            flash('Invalid time duration format. Please use HH:MM.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        # Validate other fields
        if not name:
            flash('Quiz name is required.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        # Check if quiz already exists
        quiz = Quiz.query.filter_by(name=name).first()
        if quiz:
            flash('Quiz already exists.')
            return redirect(url_for('add_quiz', chapter_id=chapter_id))

        # Get subject_id from the chapter
        subject_id = chapter.subject_id

        # Add the new quiz to the database
        new_quiz = Quiz(
            name=name,
            description=description,
            chapter_id=chapter_id,
            start_date=start_date,
            end_date=end_date,
            time_duration=time_duration,
            is_active=is_active == 'true',  # Convert string to boolean
            subject_id=subject_id
        )
        db.session.add(new_quiz)
        db.session.commit()

        flash('Quiz added successfully.')
        return redirect(url_for('quiz_dashboard'))

    return render_template('admin/manage_quiz.html',chapter_id=chapter_id, chapter=chapter, usage='add')
## Edit Quiz
@app.route('/admin/manage_quiz/edit/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def edit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    usage = 'edit'

    if request.method == 'POST':
        quiz.name = request.form.get('name')
        quiz.description = request.form.get('description')
        quiz.chapter_id = request.form.get('chapter_id')
        quiz.start_date = request.form.get('start_date')
        quiz.end_date = request.form.get('end_date')
        quiz.time_duration = request.form.get('time_duration')
        quiz.is_active = request.form.get('is_active') == 'true'

        db.session.commit()
        flash('Quiz updated successfully')
        return redirect(url_for('quiz_dashboard'))

    return render_template('admin/manage_quiz.html', quiz=quiz, usage='edit')

## Delete Quiz
@app.route('/admin/delete_quiz/<int:quiz_id>', methods=['POST'])
@admin_required
@auth_required
def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully')
    return redirect(url_for('quiz_dashboard'))

### Manage Questions
@app.route('/admin/manage_question/<int:quiz_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    usage = "add"
    if request.method == 'POST':
        title = request.form.get('title')
        question_statement = request.form.get('question_statement')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_option = request.form.get('correct_option')

        if not title or not question_statement or not option1 or not option2 or not option3 or not option4 or not correct_option:
            flash('Please fill out all fields')
            return redirect(url_for('add_question', quiz_id=quiz_id, usage='add'))
        chapter_id = quiz.chapter_id
        # Add the new question to the database
        new_question = Questions(
            title=title,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option,
            quiz_id=quiz_id,
            chapter_id=chapter_id
        )
        
        # Increment the no_of_questions column in the Quiz table
        quiz.no_of_questions = (quiz.no_of_questions or 0) + 1  # Handle None case
        db.session.commit()

        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully')
        return redirect(url_for('quiz_dashboard'))

    return render_template('admin/manage_question.html', quiz_id=quiz_id, quiz=quiz, usage='add')


# Edit Question
@app.route('/admin/manage_question/edit/<int:question_id>', methods=['GET', 'POST'])
@admin_required
@auth_required
def edit_question(question_id):
    question = Questions.query.get_or_404(question_id)
    usage = 'edit'
    if request.method == 'POST':
        question.title = request.form.get('title')
        question.question_statement = request.form.get('question_statement')
        question.option1 = request.form.get('option1')
        question.option2 = request.form.get('option2')
        question.option3 = request.form.get('option3')
        question.option4 = request.form.get('option4')
        question.correct_option = request.form.get('correct_option')

        if not question.title or not question.question_statement or not question.option1 or not question.option2 or not question.option3 or not question.option4 or not question.correct_option:
            flash('Please fill out all fields')
            return redirect(url_for('edit_question', question_id=question_id, usage='edit'))

        db.session.commit()
        flash('Question updated successfully')
        return redirect(url_for('quiz_dashboard'))

    return render_template('admin/manage_question.html', question=question, usage='edit')


# Delete Question
@app.route('/delete_question/<int:question_id>', methods=['POST'])
@admin_required
@auth_required
def delete_question(question_id):
    question = Questions.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    quiz=Quiz.query.get(question.quiz_id)
    # decrement the no_of_questions column in the Quiz table
    quiz.no_of_questions = (quiz.no_of_questions ) - 1  # Handle None case
    db.session.commit()

    flash('Question deleted successfully')
    return redirect(url_for('quiz_dashboard'))

## manage user
@app.route('/admin/manage_user')
@admin_required
def manage_user():
    # Fetch active users (not flagged)
    users = User.query.filter(User.flagged == 0, User.is_admin==False).all()

    # Fetch flagged users
    users_flagged = User.query.filter(User.flagged == 1, User.is_admin==False).all()

    # Render the template with the correct variables
    return render_template('admin/manage_user.html', users=users, qualify=users_flagged)

@app.route('/admin/flag_user/<int:user_id>')
@admin_required
def flag_user(user_id):
    user = User.query.get_or_404(user_id)
    user.flagged = True
    db.session.commit()
    flash('User flagged successfully.')
    return redirect(url_for('manage_user'))

@app.route('/admin/unflag_user/<int:user_id>')
@admin_required
def unflag_user(user_id):
    user = User.query.get_or_404(user_id)
    user.flagged = False
    db.session.commit()
    flash('User unflagged successfully.')
    return redirect(url_for('manage_user'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('manage_user'))


@app.route("/admin/summary")
@admin_required
def admin_summary():
    return render_template('admin/admin_summary.html')



