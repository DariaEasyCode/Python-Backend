# Импорты
from flask import Flask, render_template, request, redirect
import sqlite3
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

app = Flask(__name__)

# Подключение к базе данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cur = conn.cursor()

# Создание таблицы пользователей
cur.execute('''CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            password TEXT
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

cur.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON posts(user_id)')
cur.execute('CREATE INDEX IF NOT EXISTS idx_notif_user_id ON notifications(user_id)')

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
    Спасибо за регистрацию в нашем блоге.
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
    cur.execute('INSERT INTO users(name, email, password) VALUES (?, ?, ?)', [name, email, password])
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

# Добавляет новый пост с привязкой к пользователю
def add_new_post(title, content, user_id):
    cur.execute('INSERT INTO posts(title, content, user_id) VALUES (?, ?, ?)', [title, content, user_id])
    conn.commit()

# Возвращает посты пользователя
def get_posts_by_user(user_id):
    cur.execute('SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC', [user_id])
    return cur.fetchall()

# Логирует уведомление
def log_notification(user_id, action, details):
    cur.execute('INSERT INTO notifications(user_id, action, details) VALUES (?, ?, ?)',
                [user_id, action, details])
    conn.commit()

# Возвращает уведомления пользователя
def get_notifications_by_user(user_id):
    cur.execute('SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC', [user_id])
    return cur.fetchall()

# Рендерим стартовую страницу
@app.route('/')
def main():
    posts = cur.execute('SELECT posts.*, users.name FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.created_at DESC').fetchall()
    users = cur.execute('SELECT * FROM users').fetchall()
    return render_template('main.html', posts=posts, users=users)

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
        user = get_user_by_email(email)
        if user is None:
            return render_template('login.html', message="Нет такой почты")
        if user[3] == password:
            print('Вход выполнен')
            # Логируем вход
            log_notification(user[0], 'login', 'Пользователь вошел в систему')
            return redirect(f'/user/{user[0]}')
        else:
            return render_template('login.html', message="Пароль неверный")
    return render_template('login.html')

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
        user_id = 1  # Временное решение - ID первого пользователя
        add_new_post(title, content, user_id)
        # Логируем создание поста
        log_notification(user_id, 'new_post', f'Создан пост "{title}"')
        return redirect('/')
    return render_template('new_post.html')
app.run()