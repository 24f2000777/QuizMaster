# Quiz Master App

## Description
Quiz Master is a Flask-based web application that allows users to take quizzes, test their knowledge, and improve their learning experience. The app is built using Flask, Jinja2, SQLite (via Flask-SQLAlchemy), and HTML/CSS for the front-end.

## Features
- User-friendly quiz interface
- Supports multiple-choice questions
- Backend powered by Flask and Flask-SQLAlchemy
- Dynamic routing and template rendering with Jinja2
- Score tracking and feedback system
- Easy database integration with SQLite

## Installation
### Prerequisites
Ensure you have the following installed on your system:
- Python (>=3.7)
- pip (Python package manager)

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/quiz-master.git
   cd quiz-master
   ```
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```bash
   python init_db.py
   ```
5. Run the application:
   ```bash
   python app.py
   ```
6. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Usage
- Users can start a quiz from the home page.
- Each quiz consists of multiple-choice questions.
- Users receive feedback after completing the quiz.
- The app tracks scores and progress.

## Contributing
Feel free to fork the repository and submit pull requests with enhancements or bug fixes.


