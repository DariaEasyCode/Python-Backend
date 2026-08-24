# Импорты
from flask import Flask, render_template, request, redirect, session
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os
import secrets
import time
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Секретный ключ для сессий

# Подключение к базе данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cur = conn.cursor()

# Создание таблицы пользователей
cur.execute('''CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            password TEXT,
            last_login TIMESTAMP
)''')

# Создание таблицы постов
cur.execute('''CREATE TABLE IF NOT EXISTS posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
)''')

# Создание таблицы уведомлений
cur.execute('''CREATE TABLE IF NOT EXISTS notifications(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
)''')

# Создание таблицы токенов аутентификации
cur.execute('''CREATE TABLE IF NOT EXISTS auth_tokens(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
)''')

cur.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON posts(user_id)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_notif_user_id ON notifications(user_id)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_token ON auth_tokens(token)')

# Сохранение изменений в базе данных
conn.commit()

# Функция отправки welcome-письма
def send_welcome_email(to_email, username):
    # Получаем данные из переменных окружения
    from_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")    
    # Проверяем, что переменные загружены
    if not from_email or not password:
        print("ОШИБКА: EMAIL_USER или EMAIL_PASSWORD не установлены в переменных окружения!")
        return False
    subject = "Добро пожаловать в наш блог!"
    body = f"""
    Привет, {username}!
    Спасибо за регистрацию в нашем блога.
    С уважением,
    Команда блога
    """
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email    
    try:
        # Настройки для Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Включаем шифрование
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()        
        print(f"  Письмо успешно отправлено на {to_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        print(" Ошибка аутентификации. Проверьте email и пароль приложения.")
    except Exception as e:
        print(f" Ошибка отправки письма: {e}")   
    return False

# Добавляет нового пользователя и возвращает его ID
def add_user(name, email, password):
    cur.execute('INSERT INTO users(name, email, password, last_login) VALUES (?, ?, ?, ?)', 
                [name, email, password, datetime.now()])
    conn.commit()
    cur.execute('SELECT id FROM users WHERE email = ?', [email])
    return cur.fetchone()[0]

# Возвращает пользователя по его ID
def get_user_by_id(user_id):
    cur.execute('SELECT * FROM users WHERE id = ?', [user_id])
    return cur.fetchone()

# Возвращает пользователя по его электронной почте
def get_user_by_email(email):
    cur.execute('SELECT * FROM users WHERE email = ?', [email])
    return cur.fetchone()

# Обновляет время последнего входа
def update_last_login(user_id):
    cur.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                [datetime.now(), user_id])
    conn.commit()

# Добавляет новый пост с привязкой к пользователю
def add_new_post(title, content, user_id):
    cur.execute('INSERT INTO posts(title, content, user_id) VALUES (?, ?, ?)', 
                [title, content, user_id])
    conn.commit()

# Возвращает посты пользователя
def get_posts_by_user(user_id):
    cur.execute('SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC', [user_id])
    return cur.fetchall()

# Создает токен аутентификации
def create_auth_token(user_id, remember=False):
    token = secrets.token_hex(32)    
    if remember:
        expires_at = time.time() + 30 * 24 * 60 * 60  # 30 дней
    else:
        expires_at = time.time() + 60 * 60  # 1 час    
    cur.execute('INSERT INTO auth_tokens(user_id, token, expires_at) VALUES (?, ?, ?)',
                [user_id, token, expires_at])
    conn.commit()    
    return token

# Проверяет токен аутентификации
def validate_auth_token(token):
    cur.execute('SELECT user_id FROM auth_tokens WHERE token = ? AND expires_at > ?', [token, time.time()])
    result = cur.fetchone()    
    if result:
        return result[0]
    return None

# Удаляет токен аутентификации
def delete_auth_token(token):
    cur.execute('DELETE FROM auth_tokens WHERE token = ?', [token])
    conn.commit()

# Логирует уведомление
def log_notification(user_id, action, details):
    cur.execute('INSERT INTO notifications(user_id, action, details) VALUES (?, ?, ?)',
                [user_id, action, details])
    conn.commit()

# Возвращает уведомления пользователя
def get_notifications_by_user(user_id):
    cur.execute('SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC', 
                [user_id])
    return cur.fetchall()

# Middleware для проверки аутентификации
@app.before_request
def check_auth():
    if 'user_id' not in session:
        token = request.cookies.get('auth_token')
        if token:
            user_id = validate_auth_token(token)
            if user_id:
                user = get_user_by_id(user_id)
                if user:
                    session['user_id'] = user[0]
                    session['user_name'] = user[1]

# Рендерим стартовую страницу
@app.route('/')
def main():
    posts = cur.execute('''
        SELECT posts.*, users.name 
        FROM posts 
        JOIN users ON posts.user_id = users.id 
        ORDER BY posts.created_at DESC
    ''').fetchall()    
    users = cur.execute('SELECT * FROM users').fetchall()    
    user_name = None
    if 'user_id' in session:
        user_name = session['user_name']    
    return render_template('main.html', posts=posts, users=users, user_name=user_name)


# Регистрация пользователя
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user_by_email(email)        
        if user is None:
            user_id = add_user(name, email, password)
            # Отправляем письмо
            email_sent = send_welcome_email(email, name)            
            # Логируем действие
            if email_sent:
                log_notification(user_id, 'welcome_email_sent', 
                               f'Приветственное письмо отправлено на {email}')
            else:
                log_notification(user_id, 'welcome_email_failed', 
                               f'Не удалось отправить письмо на {email}')           
            return redirect('/login/')
        else:
            print('Такой пользователь уже есть')    
    return render_template('register.html')

# Процесс входа
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')        
        user = get_user_by_email(email)        
        if user is None:
            return render_template('login.html', message="Нет такой почты")        
        if user[3] == password:
            print('Вход выполнен')
            # Сохраняем в сессию
            session['user_id'] = user[0]
            session['user_name'] = user[1]            
            # Обновляем время последнего входа
            update_last_login(user[0])            
            # Если "Запомнить меня", создаем токен
            if remember:
                token = create_auth_token(user[0], remember=True)
                response = redirect(f'/user/{user[0]}')
                response.set_cookie('auth_token', token, max_age=30*24*60*60)
            else:
                response = redirect(f'/user/{user[0]}')            
            # Логируем вход
            log_notification(user[0], 'login', 'Пользователь вошел в систему')
            return response
        else:
            return render_template('login.html', message="Пароль неверный")    
    return render_template('login.html')

# Выход из системы
@app.route('/logout')
def logout():
    token = request.cookies.get('auth_token')
    if token:
        delete_auth_token(token)    
    session.clear()    
    response = redirect('/')
    response.set_cookie('auth_token', '', expires=0)    
    return response

# Страница пользователя
@app.route('/user/<int:user_id>')
def user_page(user_id):
    user = get_user_by_id(user_id)
    posts = get_posts_by_user(user_id)
    notifications = get_notifications_by_user(user_id)    
    if user:
        return render_template('user_page.html', user=user, posts=posts, notifications=notifications)    
    return "Пользователь не найден", 404

# Добавление поста
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')        
        # Используем ID из сессии
        if 'user_id' in session:
            user_id = session['user_id']
        else:
            return redirect('/login/')        
        add_new_post(title, content, user_id)
        log_notification(user_id, 'new_post', f'Создан пост "{title}"')        
        return redirect('/')    
    return render_template('new_post.html')

app.run()