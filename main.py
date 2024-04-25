import os
import sqlite3

from flask import Flask, render_template, request, redirect, session, url_for
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/images'


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    submit = SubmitField('Login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return redirect('/login')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                              (username, password)).fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect('/profile')

    return render_template('login.html', form=form)


@app.route('/create_team', methods=['GET', 'POST'])
def create_team():
    form = LoginForm()
    if request.method == 'POST':
        coach_name = request.form['coach_name']
        team_name = request.form['team_name']
        team_abbreviation = request.form['team_abbreviation']
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coach_name TEXT NOT NULL,
                team_name TEXT NOT NULL,
                team_abbreviation TEXT NOT NULL
            )
        ''')
        conn.commit()

        cursor.execute('INSERT INTO teams (coach_name, team_name, team_abbreviation) VALUES (?, ?, ?)',
                       (coach_name, team_name, team_abbreviation))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('create_team.html', form=form)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect('/login')

    username = session.get('username')
    form = LoginForm()

    if request.method == 'POST':
        avatar_file = request.files['avatar']

        if avatar_file:
            avatar_filename = secure_filename(avatar_file.filename)
            avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename))

    return render_template('profile.html', username=username, form=form)


@app.route('/matches', methods=['GET', 'POST'])
def matches():
    if request.method == 'POST':
        opponent_name = request.form['opponent_name']
        score = request.form['score']
        team_name = request.form['team_name']
        if ':' not in score or len(score.split(':')) != 2:
            return redirect(url_for('matches'))

        team_score, opponent_score = map(int, score.split(':'))
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opponent_name TEXT NOT NULL,
                team_name TEXT NOT NULL,
                team_score INTEGER NOT NULL,
                opponent_score INTEGER NOT NULL
            )
        ''')
        conn.commit()

        cursor.execute('INSERT INTO matches (opponent_name, team_name, team_score, opponent_score) VALUES (?, ?, ?, ?)',
                       (opponent_name, team_name, team_score, opponent_score))
        conn.commit()
        conn.close()
        return redirect(url_for('team_stats'))

    return render_template('matches.html')


@app.route('/team_stats')
def team_stats():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM matches')
    matches = cursor.fetchall()
    conn.close()

    return render_template('team_stats.html', matches=matches)


if __name__ == '__main__':
    app.run(debug=True)
