from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
from datetime import datetime, timedelta
import os
import random

app = Flask(__name__)
app.secret_key = 'muschansha'

# Database setup
def init_db():
    conn = sqlite3.connect('quiz_platform.db')
    c = conn.cursor()
    
    # Users table with new fields
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        points INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        badges TEXT DEFAULT '',
        streak INTEGER DEFAULT 0,
        last_quiz_date TEXT,
        total_quizzes INTEGER DEFAULT 0,
        best_streak INTEGER DEFAULT 0,
        avatar TEXT DEFAULT '🎓',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Quizzes table
    c.execute('''CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        subject TEXT,
        score INTEGER,
        total_questions INTEGER,
        difficulty TEXT,
        time_taken INTEGER,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Questions table
    c.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        difficulty TEXT,
        question TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_answer TEXT,
        explanation TEXT
    )''')
    
    # Achievements table
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        achievement_name TEXT,
        achievement_icon TEXT,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Daily challenges table
    c.execute('''CREATE TABLE IF NOT EXISTS daily_challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE,
        subject TEXT,
        difficulty TEXT,
        bonus_points INTEGER
    )''')
    
    # Challenge completions table
    c.execute('''CREATE TABLE IF NOT EXISTS challenge_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        challenge_id INTEGER,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (challenge_id) REFERENCES daily_challenges(id)
    )''')
    
    # Insert sample questions with explanations
    c.execute('SELECT COUNT(*) FROM questions')
    if c.fetchone()[0] == 0:
        sample_questions = [
            ('Math', 'easy', 'What is 5 + 3?', '6', '7', '8', '9', 'c', 'Simple addition: 5 + 3 = 8'),
            ('Math', 'easy', 'What is 10 - 4?', '5', '6', '7', '8', 'b', 'Simple subtraction: 10 - 4 = 6'),
            ('Math', 'easy', 'What is 2 × 4?', '6', '8', '10', '12', 'b', 'Multiplication: 2 × 4 = 8'),
            ('Math', 'medium', 'What is 12 × 5?', '50', '55', '60', '65', 'c', '12 × 5 = 60'),
            ('Math', 'medium', 'What is 144 ÷ 12?', '10', '11', '12', '13', 'c', '144 divided by 12 equals 12'),
            ('Math', 'medium', 'What is 15% of 200?', '20', '25', '30', '35', 'c', '15% of 200 = 0.15 × 200 = 30'),
            ('Math', 'hard', 'What is √81?', '7', '8', '9', '10', 'c', 'The square root of 81 is 9'),
            ('Math', 'hard', 'What is 2³ + 3²?', '13', '15', '17', '19', 'c', '2³ = 8, 3² = 9, so 8 + 9 = 17'),
            ('Science', 'easy', 'What planet is closest to the Sun?', 'Venus', 'Mercury', 'Mars', 'Earth', 'b', 'Mercury is the closest planet to the Sun'),
            ('Science', 'easy', 'What is H2O?', 'Oxygen', 'Hydrogen', 'Water', 'Carbon', 'c', 'H2O is the chemical formula for water'),
            ('Science', 'easy', 'How many legs does a spider have?', '6', '8', '10', '12', 'b', 'Spiders are arachnids with 8 legs'),
            ('Science', 'medium', 'What is the powerhouse of the cell?', 'Nucleus', 'Mitochondria', 'Ribosome', 'Chloroplast', 'b', 'Mitochondria produce energy (ATP) for the cell'),
            ('Science', 'medium', 'What is the speed of light?', '300,000 km/s', '150,000 km/s', '450,000 km/s', '600,000 km/s', 'a', 'Light travels at approximately 300,000 km/s in a vacuum'),
            ('Science', 'medium', 'What gas do plants absorb?', 'Oxygen', 'Nitrogen', 'CO2', 'Hydrogen', 'c', 'Plants absorb carbon dioxide (CO2) during photosynthesis'),
            ('Science', 'hard', 'What is the atomic number of Carbon?', '4', '6', '8', '12', 'b', 'Carbon has 6 protons, giving it atomic number 6'),
            ('Science', 'hard', 'What is absolute zero in Celsius?', '-273.15°C', '-100°C', '0°C', '-200°C', 'a', 'Absolute zero is -273.15°C or 0 Kelvin'),
            ('History', 'easy', 'Who was the first President of USA?', 'Jefferson', 'Washington', 'Lincoln', 'Adams', 'b', 'George Washington was the first US President (1789-1797)'),
            ('History', 'easy', 'What country is home to the pyramids?', 'Greece', 'Egypt', 'Mexico', 'India', 'b', 'The famous pyramids are in Egypt'),
            ('History', 'medium', 'In what year did World War II end?', '1943', '1944', '1945', '1946', 'c', 'World War II ended in 1945'),
            ('History', 'medium', 'Who wrote Romeo and Juliet?', 'Dickens', 'Shakespeare', 'Austen', 'Twain', 'b', 'William Shakespeare wrote Romeo and Juliet'),
            ('History', 'hard', 'What ancient wonder was in Alexandria?', 'Colossus', 'Lighthouse', 'Pyramids', 'Gardens', 'b', 'The Lighthouse of Alexandria was one of the Seven Wonders'),
            ('History', 'hard', 'When did the Berlin Wall fall?', '1987', '1989', '1991', '1993', 'b', 'The Berlin Wall fell on November 9, 1989'),
        ]
        c.executemany('INSERT INTO questions VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)', sample_questions)
    
    conn.commit()
    conn.close()

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db():
    conn = sqlite3.connect('quiz_platform.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_level(points):
    return (points // 100) + 1

def award_badge(points):
    badges = []
    if points >= 50: badges.append('🌟 Beginner')
    if points >= 150: badges.append('🏆 Intermediate')
    if points >= 300: badges.append('👑 Expert')
    if points >= 500: badges.append('💎 Master')
    if points >= 1000: badges.append('🔥 Legend')
    return ', '.join(badges)

def update_streak(user_id):
    conn = get_db()
    user = conn.execute('SELECT last_quiz_date, streak, best_streak FROM users WHERE id = ?', (user_id,)).fetchone()
    
    today = datetime.now().date().isoformat()
    last_date = user['last_quiz_date']
    current_streak = user['streak']
    best_streak = user['best_streak']
    
    if last_date:
        last_date_obj = datetime.fromisoformat(last_date).date()
        today_obj = datetime.now().date()
        diff = (today_obj - last_date_obj).days
        
        if diff == 0:
            # Same day, no change
            pass
        elif diff == 1:
            # Consecutive day, increase streak
            current_streak += 1
            if current_streak > best_streak:
                best_streak = current_streak
        else:
            # Streak broken
            current_streak = 1
    else:
        current_streak = 1
    
    conn.execute('UPDATE users SET last_quiz_date = ?, streak = ?, best_streak = ? WHERE id = ?',
                (today, current_streak, best_streak, user_id))
    conn.commit()
    conn.close()
    return current_streak

def check_achievements(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    quizzes = conn.execute('SELECT COUNT(*) as count FROM quizzes WHERE user_id = ?', (user_id,)).fetchone()
    
    achievements = []
    existing = [row['achievement_name'] for row in conn.execute('SELECT achievement_name FROM achievements WHERE user_id = ?', (user_id,)).fetchall()]
    
    # First quiz achievement
    if quizzes['count'] >= 1 and 'First Steps' not in existing:
        achievements.append(('First Steps', '🎯'))
    
    # 10 quizzes achievement
    if quizzes['count'] >= 10 and 'Quiz Master' not in existing:
        achievements.append(('Quiz Master', '📚'))
    
    # 50 quizzes achievement
    if quizzes['count'] >= 50 and 'Dedicated Learner' not in existing:
        achievements.append(('Dedicated Learner', '🎓'))
    
    # Streak achievements
    if user['streak'] >= 3 and 'Hot Streak' not in existing:
        achievements.append(('Hot Streak', '🔥'))
    
    if user['streak'] >= 7 and 'Week Warrior' not in existing:
        achievements.append(('Week Warrior', '⚡'))
    
    # Points achievements
    if user['points'] >= 500 and 'Point Master' not in existing:
        achievements.append(('Point Master', '⭐'))
    
    # Perfect score achievement
    perfect_scores = conn.execute('SELECT COUNT(*) as count FROM quizzes WHERE user_id = ? AND score = total_questions', (user_id,)).fetchone()
    if perfect_scores['count'] >= 5 and 'Perfectionist' not in existing:
        achievements.append(('Perfectionist', '💯'))
    
    # Save new achievements
    for name, icon in achievements:
        conn.execute('INSERT INTO achievements (user_id, achievement_name, achievement_icon) VALUES (?, ?, ?)',
                    (user_id, name, icon))
    
    conn.commit()
    conn.close()
    return achievements

def get_daily_challenge():
    conn = get_db()
    today = datetime.now().date().isoformat()
    
    challenge = conn.execute('SELECT * FROM daily_challenges WHERE date = ?', (today,)).fetchone()
    
    if not challenge:
        # Create new daily challenge
        subjects = ['Math', 'Science', 'History']
        difficulties = ['easy', 'medium', 'hard']
        subject = random.choice(subjects)
        difficulty = random.choice(difficulties)
        bonus_points = {'easy': 20, 'medium': 40, 'hard': 60}[difficulty]
        
        conn.execute('INSERT INTO daily_challenges (date, subject, difficulty, bonus_points) VALUES (?, ?, ?, ?)',
                    (today, subject, difficulty, bonus_points))
        conn.commit()
        challenge = conn.execute('SELECT * FROM daily_challenges WHERE date = ?', (today,)).fetchone()
    
    conn.close()
    return challenge

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        avatar = request.form.get('avatar', '🎓')
        
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (username, password, avatar) VALUES (?, ?, ?)', (username, password, avatar))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already exists')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                          (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    recent_quizzes = conn.execute('SELECT * FROM quizzes WHERE user_id = ? ORDER BY completed_at DESC LIMIT 5', 
                                 (session['user_id'],)).fetchall()
    achievements = conn.execute('SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at DESC LIMIT 6', 
                               (session['user_id'],)).fetchall()
    conn.close()
    
    daily_challenge = get_daily_challenge()
    
    # Check if user completed today's challenge
    conn = get_db()
    completed_today = conn.execute('''SELECT COUNT(*) as count FROM challenge_completions cc
                                     JOIN daily_challenges dc ON cc.challenge_id = dc.id
                                     WHERE cc.user_id = ? AND dc.date = ?''',
                                  (session['user_id'], datetime.now().date().isoformat())).fetchone()
    conn.close()
    
    challenge_completed = completed_today['count'] > 0
    
    return render_template('dashboard.html', user=user, recent_quizzes=recent_quizzes, 
                         achievements=achievements, daily_challenge=daily_challenge,
                         challenge_completed=challenge_completed)

@app.route('/quiz/<subject>/<difficulty>')
def quiz(subject, difficulty):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    is_daily = request.args.get('daily') == 'true'
    
    conn = get_db()
    questions = conn.execute('SELECT * FROM questions WHERE subject = ? AND difficulty = ? ORDER BY RANDOM() LIMIT 5', 
                            (subject, difficulty)).fetchall()
    conn.close()
    
    return render_template('quiz.html', questions=questions, subject=subject, difficulty=difficulty, is_daily=is_daily)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    data = request.json
    score = data['score']
    total = data['total']
    subject = data['subject']
    difficulty = data['difficulty']
    time_taken = data.get('time_taken', 0)
    is_daily = data.get('is_daily', False)
    
    # Calculate points
    multiplier = {'easy': 10, 'medium': 20, 'hard': 30}
    points_earned = score * multiplier[difficulty]
    
    # Bonus for perfect score
    if score == total:
        points_earned += 20
    
    # Bonus for daily challenge
    daily_bonus = 0
    if is_daily:
        challenge = get_daily_challenge()
        daily_bonus = challenge['bonus_points']
        points_earned += daily_bonus
        
        # Mark challenge as completed
        conn = get_db()
        conn.execute('INSERT INTO challenge_completions (user_id, challenge_id) VALUES (?, ?)',
                    (session['user_id'], challenge['id']))
        conn.commit()
        conn.close()
    
    conn = get_db()
    # Save quiz result
    conn.execute('INSERT INTO quizzes (user_id, subject, score, total_questions, difficulty, time_taken) VALUES (?, ?, ?, ?, ?, ?)',
                (session['user_id'], subject, score, total, difficulty, time_taken))
    
    # Update user stats
    user = conn.execute('SELECT points, total_quizzes FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    new_points = user['points'] + points_earned
    new_level = calculate_level(new_points)
    new_badges = award_badge(new_points)
    new_total = user['total_quizzes'] + 1
    
    conn.execute('UPDATE users SET points = ?, level = ?, badges = ?, total_quizzes = ? WHERE id = ?',
                (new_points, new_level, new_badges, new_total, session['user_id']))
    conn.commit()
    conn.close()
    
    # Update streak
    new_streak = update_streak(session['user_id'])
    
    # Check for new achievements
    new_achievements = check_achievements(session['user_id'])
    
    return jsonify({
        'success': True, 
        'points_earned': points_earned,
        'total_points': new_points,
        'level': new_level,
        'streak': new_streak,
        'daily_bonus': daily_bonus,
        'perfect_bonus': 20 if score == total else 0,
        'new_achievements': [{'name': name, 'icon': icon} for name, icon in new_achievements]
    })

@app.route('/leaderboard')
def leaderboard():
    conn = get_db()
    users = conn.execute('SELECT username, points, level, badges, streak, avatar FROM users ORDER BY points DESC LIMIT 10').fetchall()
    conn.close()
    
    return render_template('leaderboard.html', users=users)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Statistics
    total_quizzes = conn.execute('SELECT COUNT(*) as count FROM quizzes WHERE user_id = ?', (session['user_id'],)).fetchone()
    avg_score = conn.execute('SELECT AVG(CAST(score AS FLOAT) / total_questions * 100) as avg FROM quizzes WHERE user_id = ?', (session['user_id'],)).fetchone()
    best_subject = conn.execute('''SELECT subject, AVG(CAST(score AS FLOAT) / total_questions * 100) as avg 
                                  FROM quizzes WHERE user_id = ? GROUP BY subject ORDER BY avg DESC LIMIT 1''', (session['user_id'],)).fetchone()
    
    achievements = conn.execute('SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at DESC', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('profile.html', user=user, total_quizzes=total_quizzes, 
                         avg_score=avg_score, best_subject=best_subject, achievements=achievements)

@app.route('/achievements')
def achievements():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    user_achievements = conn.execute('SELECT * FROM achievements WHERE user_id = ? ORDER BY earned_at DESC', 
                                    (session['user_id'],)).fetchall()
    conn.close()
    
    # All possible achievements
    all_achievements = [
        {'name': 'First Steps', 'icon': '🎯', 'description': 'Complete your first quiz'},
        {'name': 'Quiz Master', 'icon': '📚', 'description': 'Complete 10 quizzes'},
        {'name': 'Dedicated Learner', 'icon': '🎓', 'description': 'Complete 50 quizzes'},
        {'name': 'Hot Streak', 'icon': '🔥', 'description': 'Maintain a 3-day streak'},
        {'name': 'Week Warrior', 'icon': '⚡', 'description': 'Maintain a 7-day streak'},
        {'name': 'Point Master', 'icon': '⭐', 'description': 'Earn 500 points'},
        {'name': 'Perfectionist', 'icon': '💯', 'description': 'Get 5 perfect scores'},
    ]
    
    earned_names = [ach['achievement_name'] for ach in user_achievements]
    
    return render_template('achievements.html', user_achievements=user_achievements, 
                         all_achievements=all_achievements, earned_names=earned_names)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))




if __name__ == '__main__':
    init_db()
    app.run(debug=True)