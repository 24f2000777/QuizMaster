from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func

db = SQLAlchemy()

class Users(db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True,nullable=False,autoincrement=True)
    fullname=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(200),unique=True,nullable=False)
    password=db.Column(db.String(100),nullable=False)

class Subjects(db.Model):
    __tablename__="subjects"
    id=db.Column(db.Integer,primary_key=True,nullable=False,unique=True,autoincrement=True)
    name=db.Column(db.String(100),nullable=False,unique=True)
    description=db.Column(db.Text,nullable=True)
    chapters = db.relationship('Chapter', backref='subject', lazy=True)

class Chapter(db.Model):
    __tablename__="chapter"
    id=db.Column(db.Integer,primary_key=True,nullable=False,unique=True,autoincrement=True)
    subject_id=db.Column(db.Integer,db.ForeignKey('subjects.id'),nullable=False)
    name=db.Column(db.String(100),nullable=False)
    number_of_questions = db.Column(db.Integer, nullable=False)  
    quizzes=db.relationship('Quiz',backref='chapter',lazy=True,cascade="all, delete-orphan")

class Quiz(db.Model):
    __tablename__="quiz"
    id=db.Column(db.Integer,primary_key=True,nullable=False,unique=True,autoincrement=True)
    chapter_id=db.Column(db.Integer,db.ForeignKey('chapter.id'),nullable=False)
    title=db.Column(db.String(100),nullable=False)
    description=db.Column(db.Text,nullable=False)
    max_questions = db.Column(db.Integer, nullable=False, default=5)
    number_of_questions = db.Column(db.Integer, nullable=False)  
    duration = db.Column(db.Integer, nullable=False)  
    quiz_date = db.Column(db.DateTime, nullable=False, default=func.now())
    questions=db.relationship('Questions',backref='quiz', cascade="all, delete-orphan",lazy=True)
    
class Questions(db.Model):
    __tablename__="questions"
    id=db.Column(db.Integer,primary_key=True,nullable=False,unique=True,autoincrement=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id',ondelete="cascade"), nullable=False)
    question_text = db.Column(db.String(300), nullable=False)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    option_c = db.Column(db.String(100), nullable=False)
    option_d = db.Column(db.String(100), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)


class Score(db.Model):
    __tablename__="score"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', ondelete="CASCADE"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    quiz = db.relationship('Quiz', backref=db.backref('scores', cascade="all, delete-orphan", lazy=True))


