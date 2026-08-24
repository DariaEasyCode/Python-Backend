#Импорты
from flask import Flask, render_template, request, redirect
import sqlite3


#Создание приложения
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


#Сохранение изменений в базе данных
conn.commit()


#Добавляет нового пользователя в таблицу users
def add_user(name, email, password):
    cur.execute('INSERT INTO users(name, email, password) VALUES (?, ?, ?)', [name, email, password])
    conn.commit()


#Возвращает пользователя по его ID
def get_user_by_id(user_id):
    cur.execute(f'SELECT * FROM users WHERE id = {user_id}')
    return cur.fetchone()


#Возвращает пользователя по его электронной почте
def get_user_by_email(email):
    cur.execute(f'SELECT * FROM users WHERE email = ?', [email])
    return cur.fetchone()


#Рендерим стартовую страницу
@app.route('/')
def main():
   return  render_template('main.html')


#Регистрация пользователя
@app.route('/register/', methods=['GET', 'POST'])
def register():
    #Проверяется, является ли метод запроса POST
    if request.method == 'POST':
        #Получение данных из формы
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user_by_email(email)
        #Проверка существования пользователя


        if user is None: #Если пользователь не существует
            add_user(name, email, password) #Добавление нового пользователя
            return redirect('/profile/') #Перенаправление
        else:
            print('Такой пользователь уже есть') #Обработка существующего пользователя


    return render_template('register.html') #Отображение страницы регистрации (Если метод запроса — GET)


#Процесс входа
@app.route('/login/', methods=['GET', 'POST'])
def login():
    #Проверяется, является ли метод запроса POST
    if request.method == 'POST':
        #Получение данных из формы
        email = request.form.get('email')
        password = request.form.get('password')


        #Проверка существования пользователя
        user = get_user_by_email(email)


       
        if user is None: #Если пользователь не существует
            return render_template('login.html', message="Нет такой почты")
        #Если пользователя с указанным email нет в базе данных - возвращается HTML-шаблон login.html,
        # и передается сообщение о том, что такой почты нет
       
        if user[3] == password: #Проверка пароля
            print('Вход выполнен') #Сообщение о входе
            return redirect('/profile/') #Перенаправление    
        else: #Если пароль неверный
            return render_template('login.html', message="Пароль неверный") #Возвращение шаблона
       
    return render_template('login.html') #Возвращение шаблона


#Рендерим страницу профиля пользователя
@app.route('/profile/')
def profile():
    return render_template('profile.html')


app.run() #Запуск
