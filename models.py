from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
db=SQLAlchemy(app)

class User(db.Model):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    passhash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    qualification = db.Column( db.String(64), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.passhash=generate_password_hash(password)
                                             
    def check_password(self, password):
        return check_password_hash(self.passhash, password)
    
class Subject(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(32), unique=True)
    Description=db.Column(db.String(256), nullable=False)
    category=db.Column(db.String(32), nullable=False)
    
    
class Chapter(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(32), unique=True)
    Description=db.Column(db.String(256), nullable=False)
    
    subject_id=db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)    

class Quiz(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    date_of_quiz=db.Column(db.Date, nullable=False)
    time_duration=db.Column(db.Time, nullable=False)
    remarks=db.Column(db.String(256), nullable=False)
    chapter_id= db.Column(db.Integer, db.ForeignKey('chapter.id'),nullable=False)
    
class Questions(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    question_statement=db.Column(db.String(256), nullable=False)
    option1=db.Column(db.String(64), nullable=False)
    option2=db.Column(db.String(64), nullable=False)
    option3=db.Column(db.String(64), nullable=False)
    option4=db.Column(db.String(64), nullable=False)
    correct_option=db.Column(db.String(64), nullable=False)
    
    quiz_id=db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    
    chapter_id=db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    
class Scores(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    time_stamp_of_attempt=db.Column(db.DateTime, nullable=False)
    score=db.Column(db.Integer, nullable=False)
    
    quiz_id=db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
with app.app_context():
    db.create_all()
    
    # create admin if admin not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        password_hash=generate_password_hash('admin')
        admin=User(username='admin', passhash=password_hash, name='admin',qualification='admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()