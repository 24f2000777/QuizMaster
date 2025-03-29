import os
import matplotlib.pyplot as plt
from matplotlib import rcParams
from flask import Flask, render_template, request, url_for, redirect, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash 
from models import db, Users, Subjects, Chapter, Quiz, Questions, Score 

app = Flask(__name__, template_folder='Templates')

app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizmaster.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")


@app.route('/')
def home():
    return render_template("landingpage.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        if role == "admin":
            admin_email = "admin@example.com"
            admin_password = "admin123"
          
            hashed_admin_password = generate_password_hash(admin_password)
            
            if email == admin_email and check_password_hash(hashed_admin_password, password):
                session["username"] = email
                flash("Admin Login successful", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("invalid Admin credentials", "danger")
                return redirect(url_for('login'))

        if role == "user":
            user = Users.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):  
                session['fullname'] = user.fullname
                session["username"] = user.email
                flash("Login Successful", "success")
                return redirect(url_for('userDashboard'))
            else:
                flash("Invalid Username or Password", "danger")
                return redirect(url_for('login'))

    return render_template("login.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        password = request.form['password']

        existing_user = Users.query.filter_by(email=email).first()
        if existing_user:
            flash("Username Already exists, please Choose a different Username", "danger")
            return redirect(url_for('signup'))
        else:
           
            hashed_password = generate_password_hash(password)
            new_user = Users(fullname=fullname, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created Successfully", "success")
            return redirect(url_for('login'))

    return render_template("signup.html")


@app.route('/userDashboard')
def userDashboard():
    if 'username' not in session:
        flash("Please login First", "danger")
        return redirect(url_for("login"))
    
    fullname = session.get('fullname', '')
    username = session.get('username', '')
    quizzes = Quiz.query.all()

    search_results = {
        'query': '',
        'subjects': [],
        'quizzes': [],
        'is_search': False
    }
    
    return render_template(
        "userDashboard.html",
        quizzes=quizzes,
        username=username,
        fullname=fullname,
        search_results=search_results
    )

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if session.get('username') != 'admin@example.com':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    
    subjects = Subjects.query.all()

    search_results = {
        'query': '',
        'subjects': [],
        'quizzes': [],
        'users': [],
        'is_search': False
    }
    
    return render_template("adminDashboard.html", subjects=subjects, search_results=search_results)


@app.route("/scores")
def scores():
    if "username" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))

    user = Users.query.filter_by(email=session["username"]).first()
    all_scores = Score.query.filter_by(user_id=user.id).order_by(Score.id.desc()).all()
    
    latest_quiz_id = session.get("latest_quiz_id")
    latest_results = session.get("latest_results", [])
    
    
    scores_data = []
    for score in all_scores:
        quiz = Quiz.query.get(score.quiz_id)  
        if quiz:  
            scores_data.append({
                'quiz_title': quiz.title,
                'score': score.score,
                'date': quiz.quiz_date if hasattr(quiz, 'quiz_date') else 'N/A',
                'total_questions': quiz.number_of_questions
            })
        else:
            
            scores_data.append({
                'quiz_title': 'Deleted Quiz',
                'score': score.score,
                'date': 'N/A',
                'total_questions': 'N/A'
            })

    return render_template(
        "scores.html",
        scores=scores_data,
        latest_results=latest_results if latest_quiz_id else [],
        latest_quiz=Quiz.query.get(latest_quiz_id) if latest_quiz_id else None
    )

@app.route("/addsubject", methods=["POST", "GET"])
def addSubject():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")

        if not name and not description:
            flash("Both fields are required", "warning")
            return redirect(url_for('addSubject'))
        elif Subjects.query.filter_by(name=name).first():
            flash("Subject already exists", "danger")
            return redirect(url_for('addSubject'))
        else:
            new_subject = Subjects(name=name, description=description)
            db.session.add(new_subject)
            db.session.commit()
            flash("Subject added successfully", "success")
            return redirect(url_for('admin_dashboard'))
    return render_template("addsubject.html")


@app.route('/admin/subject/delete/', methods=["POST"])
def delete_subject():
    subject_id = request.form.get("subject_id")

    if not subject_id:
        flash("No subject selected", "danger")
        return redirect(url_for('admin_dashboard'))
    subject = Subjects.query.get(subject_id)
    if not subject:
        flash("Subject does not exist", "danger")
    elif subject.chapters:
        flash("First delete all chapters before deleting the subject", "warning")
        return redirect(url_for('admin_dashboard'))
    else:
        db.session.delete(subject)
        db.session.commit()
        flash("Subject deleted successfully", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/chapter/add/<int:subject_id>', methods=["GET", "POST"])
def addchapter(subject_id):
    subject = Subjects.query.get(subject_id)
    if request.method == "POST":
        chapter_name = request.form.get('chapter_name')
        number_of_questions = request.form.get('number_of_questions')

        existing_chapter = Chapter.query.filter_by(subject_id=subject_id, name=chapter_name).first()
        if existing_chapter:
            flash(f"Chapter {chapter_name} already exists under this subject", "danger")
            return redirect(url_for('addchapter', subject_id=subject_id))
        else:
            new_chapter = Chapter(name=chapter_name, number_of_questions=number_of_questions, subject_id=subject_id)
            db.session.add(new_chapter)
            db.session.commit()
            flash(f"Chapter {chapter_name} added successfully", "success")
            return redirect(url_for('admin_dashboard'))
    return render_template("addchapter.html", subject=subject)


@app.route('/admin/chapter/delete/<int:id>', methods=["GET", "POST"])
def delete_chapter(id):
    chapter = Chapter.query.get(id)
    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter deleted successfully", "success")
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/chapter/edit/<int:id>", methods=["GET", "POST"])
def edit_chapter(id):
    chapter = Chapter.query.get_or_404(id)
    if not chapter:
        flash("Chapter not found", "danger")
        return redirect(url_for('admin_dashboard'))
    if request.method == "POST":
        chapter_name = request.form.get("chapter_name")
        number_of_questions = request.form.get("number_of_questions")
        if chapter_name:
            chapter.name = chapter_name
        if number_of_questions:
            chapter.number_of_questions = number_of_questions
        db.session.commit()
        flash("Chapter details updated successfully", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template("editchapter.html", chapter=chapter)


if not os.path.exists('static'):
    os.makedirs('static')

@app.route('/summary')
def summary():
    if 'username' not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))


    is_admin = session.get('username') == 'admin@example.com'
    user = Users.query.filter_by(email=session["username"]).first()


    plt.switch_backend('Agg')


    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['Poppins', 'Arial', 'DejaVu Sans']
    rcParams['font.size'] = 10 

    if is_admin:

        total_users = Users.query.count()
        total_quizzes = Quiz.query.count()
        total_subjects = Subjects.query.count()


        subjects = Subjects.query.all()
        subject_stats = []
        subject_names = []
        avg_scores = []
        for subject in subjects:

            quizzes = Quiz.query.join(Chapter).filter(Chapter.subject_id == subject.id).all()
            if quizzes:
                quiz_ids = [quiz.id for quiz in quizzes]
                scores = Score.query.filter(Score.quiz_id.in_(quiz_ids)).all()
                if scores:
                    avg_score = sum(score.score for score in scores) / len(scores)
                    subject_stats.append({
                        'subject_name': subject.name,
                        'avg_score': round(avg_score, 2),
                        'quiz_count': len(quizzes)
                    })
                    subject_names.append(subject.name)
                    avg_scores.append(avg_score)


        chart_path = None
        if subject_names and avg_scores:
            plt.figure(figsize=(10, 6))
            bars = plt.bar(subject_names, avg_scores, color='#00796b', edgecolor='#004d40', width=0.6)
            plt.xlabel('Subject', fontsize=12, color='#333', labelpad=10)
            plt.ylabel('Average Score (%)', fontsize=12, color='#333', labelpad=10)
            plt.title('Average Quiz Scores per Subject', fontsize=14, color='#00796b', pad=15)
            plt.ylim(0, 100)
            plt.xticks(rotation=30, ha='right', fontsize=8)  
            plt.yticks(fontsize=8)
            plt.grid(True, axis='y', linestyle='--', alpha=0.7)


            for bar in bars:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{yval:.1f}', ha='center', va='bottom', fontsize=8)

            plt.tight_layout(pad=2.0)  
            chart_path = 'static/admin_summary_chart.png'
            plt.savefig(chart_path, dpi=100, bbox_inches='tight')  
            plt.close()

        return render_template(
            "summary.html",
            is_admin=True,
            total_users=total_users,
            total_quizzes=total_quizzes,
            total_subjects=total_subjects,
            chart_path=chart_path
        )
    else:
        
        scores = Score.query.filter_by(user_id=user.id).all()
        quiz_performance = []
        quiz_titles = []
        user_scores = []
        for score in scores:
            quiz = Quiz.query.get(score.quiz_id)
            quiz_performance.append({
                'quiz_title': quiz.title,
                'score': score.score,
                'subject': quiz.chapter.subject.name if quiz.chapter else "N/A"
            })
            quiz_titles.append(f"{quiz.title} ({quiz.chapter.subject.name if quiz.chapter else 'N/A'})")
            user_scores.append(score.score)

       
        chart_path = None
        if quiz_titles and user_scores:
            plt.figure(figsize=(10, 6))
            bars = plt.bar(quiz_titles, user_scores, color='#ffcc00', edgecolor='#ffb300', width=0.6)
            plt.xlabel('Quiz (Subject)', fontsize=12, color='#333', labelpad=10)
            plt.ylabel('Your Score (%)', fontsize=12, color='#333', labelpad=10)
            plt.title('Your Quiz Performance', fontsize=14, color='#00796b', pad=15)
            plt.ylim(0, 100)
            plt.xticks(rotation=30, ha='right', fontsize=8)  
            plt.yticks(fontsize=8)
            plt.grid(True, axis='y', linestyle='--', alpha=0.7)

          
            for bar in bars:
                yval = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{yval:.1f}', ha='center', va='bottom', fontsize=8)

            plt.tight_layout(pad=2.0)  
            chart_path = 'static/user_summary_chart.png'
            plt.savefig(chart_path, dpi=100, bbox_inches='tight')  
            plt.close()

        return render_template(
            "summary.html",
            is_admin=False,
            quiz_performance=quiz_performance,
            chart_path=chart_path,
            fullname=user.fullname
        )


@app.route("/quiz/attempt/<int:quiz_id>", methods=["GET", "POST"])
def attempt_quiz(quiz_id):
    if "username" not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()

    if not questions:
        flash("No questions available for this quiz", "warning")
        return redirect(url_for("userDashboard"))

    if request.method == 'POST':
        user = Users.query.filter_by(email=session["username"]).first()
        total_questions = len(questions)
        question_results = []

        
        existing_score = Score.query.filter_by(user_id=user.id, quiz_id=quiz_id).first()
        if existing_score:
            db.session.delete(existing_score)
            db.session.commit()

        dict={ 'A':1,
                'B':2,
                'C':3,
                'D':4 }
        for question in questions:
            user_answer = request.form.get(f"answer_{question.id}")
            is_correct = False
            
            if dict[user_answer] ==int(question.correct_answer):
                is_correct = True
            
                
            question_results.append({
                'question': question.question_text,
                'correct': is_correct,
                'marks': 1 if is_correct else 0,
                'correct_answer': question.correct_answer,
                'user_answer': user_answer
            })

       
        correct_answers = sum(1 for result in question_results if result['correct'])
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        
        new_score = Score(
            user_id=user.id,
            quiz_id=quiz_id,
            score=int(score_percentage)  
        )
        
        db.session.add(new_score)
        db.session.commit()

        session["latest_quiz_id"] = quiz_id
        session["latest_results"] = question_results  

        flash(f"Quiz complete! Your score: {correct_answers}/{total_questions} ({score_percentage:.2f}%)", "success")
        return redirect(url_for("scores"))

    return render_template("quiz_attempt.html", quiz=quiz, questions=questions)


@app.route('/admin/quiz/add', methods=['GET', 'POST'])
def add_quiz():
    if 'username' not in session or session.get('username') != 'admin@example.com':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))

    subjects = Subjects.query.all()
    chapters = Chapter.query.all()

    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        chapter_id = request.form.get('chapter_id')
        title = request.form.get('title')
        description = request.form.get('description')
        number_of_questions = request.form.get('number_of_questions')
        duration = request.form.get('duration')

        
        if not all([subject_id, chapter_id, title, description, number_of_questions, duration]):
            flash("All fields are required", "warning")
            return redirect(url_for('add_quiz'))

        try:
            number_of_questions = int(number_of_questions)
            duration = int(duration)
        except ValueError:
            flash("Number of questions and duration must be numbers", "danger")
            return redirect(url_for('add_quiz'))

        
        chapter = Chapter.query.get(chapter_id)
        if chapter.subject_id != int(subject_id):
            flash("Selected chapter does not belong to selected subject", "danger")
            return redirect(url_for('add_quiz'))

        
        new_quiz = Quiz(
            chapter_id=chapter_id,
            title=title,
            description=description,
            number_of_questions=number_of_questions,
            duration=duration
        )
        db.session.add(new_quiz)
        db.session.commit()

        flash("Quiz added successfully", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template("addquiz.html", subjects=subjects, chapters=chapters)

@app.route('/admin/quiz')
def quiz():
    quizzes = Quiz.query.all()
    return render_template("quiz.html", quizzes=quizzes)

@app.route('/admin/delete_quiz/<int:quiz_id>', methods=["POST"])
def delete_quiz(quiz_id):
    try:
      
        Score.query.filter_by(quiz_id=quiz_id).delete()
        
        
        quiz = Quiz.query.get(quiz_id)
        if quiz:
            db.session.delete(quiz)
            db.session.commit()
            flash("Quiz deleted successfully", "success")
        else:
            flash("Quiz not found", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting quiz: {str(e)}", "danger")
    
    return redirect(url_for('quiz'))
@app.route('/admin/add_question/<int:quiz_id>', methods=["GET", "POST"])
def add_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if len(quiz.questions) >= quiz.max_questions:
        flash("Cannot add more questions. Maximum limit reached!", "warning")
        return redirect(url_for('admin_dashboard'))

    if request.method == "POST":
        question = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_answer = request.form['correct_answer']

        new_question = Questions(quiz_id=quiz_id,
                                 question_text=question,
                                 option_a=option1,
                                 option_b=option2,
                                 option_c=option3,
                                 option_d=option4,
                                 correct_answer=correct_answer)
        db.session.add(new_question)
        db.session.commit()
        flash("Question added successfully", "success")
        return redirect(url_for('quiz'))
    return render_template("add_question.html", quiz=quiz)

@app.route('/quiz/<int:quiz_id>/edit_question', methods=['GET', 'POST'])
def edit_question(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        question_id = request.form.get('question_id')
        if question_id:
            selected_question = Questions.query.get(question_id)
            if selected_question and selected_question.quiz_id == quiz_id:
                return render_template('edit_question.html', quiz=quiz, selected_question=selected_question)
            else:
                flash('Invalid question selected.', 'danger')

    
    selected_question = quiz.questions[0] if quiz.questions else None
    return render_template('edit_question.html', quiz=quiz, selected_question=selected_question)

@app.route('/update_question/<int:quiz_id>/<int:question_id>', methods=['POST'])
def update_question(quiz_id, question_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    selected_question = Questions.query.get_or_404(question_id)

    if selected_question.quiz_id != quiz_id:
        flash('Question does not belong to this quiz.', 'danger')
        return redirect(url_for('edit_question', quiz_id=quiz_id))

    
    selected_question.question_text = request.form['question_text']

    
    selected_question.option_a = request.form['option_a']
    selected_question.option_b = request.form['option_b']
    selected_question.option_c = request.form['option_c']
    selected_question.option_d = request.form['option_d']

    
    correct_option = request.form.get('correct_option')
    if correct_option:
        if correct_option == "A":
            selected_question.correct_answer = selected_question.option_a
        elif correct_option == "B":
            selected_question.correct_answer = selected_question.option_b
        elif correct_option == "C":
            selected_question.correct_answer = selected_question.option_c
        elif correct_option == "D":
            selected_question.correct_answer = selected_question.option_d
    

    db.session.commit()
    flash('Question updated successfully!', 'success')
    return redirect(url_for('edit_question', quiz_id=quiz_id))

@app.route('/delete_question/<int:quiz_id>/<int:question_id>', methods=['POST'])
def delete_question(quiz_id, question_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    question = Questions.query.get_or_404(question_id)

    if question.quiz_id != quiz_id:
        flash('Question does not belong to this quiz.', 'danger')
        return redirect(url_for('edit_question', quiz_id=quiz_id))

    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully ', 'success')
    return redirect(url_for('edit_question', quiz_id=quiz_id))



@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    if session.get('username') != 'admin@example.com':
        flash("Admin access required", "danger")
        return redirect(url_for('login'))
    
    subjects = Subjects.query.all()   
    search_results = {
        'query': '',
        'subjects': [],
        'quizzes': [],
        'users': [],
        'is_search': False
    }
    
    if request.method == 'POST':
        query = request.form.get('query', '').lower()
        category = request.form.get('category', 'all').lower()
        
        if not query:
            flash("Please enter a search term", "warning")
            return redirect(url_for('admin_dashboard'))
        
     
        
        if category == 'user' or category == 'all':
            search_results['users'] = Users.query.filter(
                (Users.fullname.ilike(f'%{query}%')) | 
                (Users.email.ilike(f'%{query}%'))
            ).all()
        if category == 'subject' or category == 'all':
            search_results['subjects'] = Subjects.query.filter(Subjects.name.ilike(f'%{query}%')).all()
        if category == 'quiz' or category == 'all':
            search_results['quizzes'] = Quiz.query.filter(
                (Quiz.title.ilike(f'%{query}%')) | 
                (Quiz.description.ilike(f'%{query}%'))
            ).all()
        
        total_results = len(search_results['subjects']) + len(search_results['quizzes']) + len(search_results['users'])
        
        if total_results == 0:
            flash(f'No results found for "{query}"', 'info')
        else:
            flash(f'found {total_results} Results For "{query}"', 'success')
        
        search_results['query'] = query
        search_results['is_search'] = True
    
    return render_template(
        'adminDashboard.html',
        subjects=subjects,
        search_results=search_results
    )

@app.route('/user/search', methods=['GET', 'POST'])
def user_search():
    if 'username' not in session:
        flash("Please login first", "danger")
        return redirect(url_for("login"))
    
    fullname = session.get('fullname', '')
    username = session.get('username', '')
    quizzes = Quiz.query.all() 
    search_results = {
        'query': '',
        'subjects': [],
        'quizzes': [],
        'is_search': False
    }
    
    if request.method == 'POST':
        query = request.form.get('query', '').lower()
        category = request.form.get('category', 'all').lower()
        
        if not query:
            flash("Please enter a search term", "warning")
            return redirect(url_for('userDashboard'))
        
        
        
        if category == 'subject' or category == 'all':
            search_results['subjects'] = Subjects.query.filter(Subjects.name.ilike(f'%{query}%')).all()
        if category == 'quiz' or category == 'all':
            search_results['quizzes'] = Quiz.query.filter(
                (Quiz.title.ilike(f'%{query}%')) | 
                (Quiz.description.ilike(f'%{query}%'))
            ).all()
        
        total_results = len(search_results['subjects']) + len(search_results['quizzes'])
        
        if total_results == 0:
            flash(f'No results found for "{query}"', 'info')
        else:
            flash(f'Found {total_results} results for "{query}"', 'success')
        
        search_results['query'] = query
        search_results['is_search'] = True
    
    return render_template(
        'userDashboard.html',
        quizzes=quizzes,
        username=username,
        fullname=fullname,
        search_results=search_results
    )
if __name__ == '__main__':
    app.run(debug=True)