#Импорты
from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

#Подключение к базе данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cur = conn.cursor()

#Создание таблицы пользователей
cur.execute('''CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            password TEXT
)''')

#Создание таблицы постов (обновлённая)
cur.execute('''CREATE TABLE IF NOT EXISTS posts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            user_id INTEGER
)''')

cur.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON posts(user_id)')

#Сохранение изменений в базе данных
conn.commit()

#Добавляет нового пользователя в таблицу users
def add_user(name, email, password):
    cur.execute('INSERT INTO users(name, email, password) VALUES (?, ?, ?)', [name, email, password])
    conn.commit()

#Возвращает пользователя по его ID
def get_user_by_id(user_id):
    cur.execute('SELECT * FROM users WHERE id = ?', [user_id])
    return cur.fetchone()

#Возвращает пользователя по его электронной почте
def get_user_by_email(email):
    cur.execute('SELECT * FROM users WHERE email = ?', [email])
    return cur.fetchone()

#Добавляет новый пост с привязкой к пользователю
def add_new_post(title, content, user_id):
    cur.execute('INSERT INTO posts(title, content, user_id) VALUES (?, ?, ?)', [title, content, user_id])
    conn.commit()

#Возвращает посты пользователя
def get_posts_by_user(user_id):
    cur.execute('SELECT * FROM posts WHERE user_id = ?', [user_id])
    return cur.fetchall()

#Рендерим стартовую страницу
@app.route('/')
def main():
    posts = cur.execute('SELECT * FROM posts ORDER BY id DESC').fetchall()
    users = cur.execute('SELECT * FROM users').fetchall()
    return render_template('main.html', posts=posts, users=users)

#Регистрация пользователя
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user_by_email(email)
        if user is None:
            add_user(name, email, password)
            return redirect('/login/')
        else:
            print('Такой пользователь уже есть')
    return render_template('register.html')

#Процесс входа
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
            return redirect(f'/user/{user[0]}')
        else:
            return render_template('login.html', message="Пароль неверный")
    return render_template('login.html')

#Рендерим страницу профиля пользователя
@app.route('/profile/')
def profile():
    return render_template('profile.html')

#Добавление поста (ВРЕМЕННО без привязки к пользователю)
@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        user_id = 1  # Временное решение - ID первого пользователя
        add_new_post(title, content, user_id)
        return redirect('/')
    return render_template('new_post.html')

#Страница пользователя
@app.route('/user/<int:user_id>')
def user_page(user_id):
    user = get_user_by_id(user_id)
    posts = get_posts_by_user(user_id)
    if user:
        return render_template('user_page.html', user=user, posts=posts)
    return "Пользователь не найден", 404

app.run()