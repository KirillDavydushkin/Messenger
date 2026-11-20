from chat_app.models import Chat
import flask
import werkzeug.security
from chat_app.models import User
import flask_login
from chat_app.mail import make_token, read_token, send_confirmation_email

from app.db import DATABASE
import werkzeug
from chat_app.models import User


def render_chat():
    
    if flask_login.current_user.is_authenticated:
        
        chats = Chat.query.all()
        
        data = {
            "can_logout": True,
            "chats": chats
        }
        
        return flask.render_template("chat.html", **data)
    
    return flask.render_template("chat.html")

def render_reg():
    
    if flask_login.current_user.is_authenticated: 
        return flask.redirect("/")
        

    if flask.request.method == "POST":
        email = flask.request.form.get("email")
        password = flask.request.form.get("password")
        
        if not (email and password):
            return flask.render_template(
                "registration.html", 
                error = "Заповніть усі поля",
                email = email
            )
        
        if User.query.filter_by(email = email).first():
            return flask.render_template(
                "registration.html", 
                error = "Користувач з такою поштою вже існує",
                email = email
            )
        
        # Користувача в базу НЕ додаємо: поки пошта не підтверджена,
        # дані (пошта + хеш пароля) лежать лише у підписаному токені
        password_hash = werkzeug.security.generate_password_hash(password)
        token = make_token(email, password_hash)
        
        # Посилання з кнопки «Підтвердити пошту» в листі
        confirm_url = flask.url_for(
            "render_confirm_email", 
            token = token, 
            _external = True
        )
        
        try:
            send_confirmation_email(email, confirm_url)
        except Exception as error:
            print(f"Помилка відправки листа: {error}")
            return flask.render_template(
                "registration.html", 
                error = "Не вдалося надіслати лист. Спробуйте пізніше",
                email = email
            )
        
        return flask.render_template(
            "registration.html", 
            success = f"Лист із посиланням для підтвердження надіслано на {email}",
            email = email
        )
    
    return flask.render_template("registration.html")


def render_confirm_email(token):
    
    # Перевіряємо підпис і термін дії посилання з листа
    data = read_token(token)
    
    if data is None:
        return flask.render_template(
            "registration.html", 
            error = "Посилання недійсне або застаріло. Зареєструйтесь ще раз"
        )
    
    # Якщо за цим посиланням уже реєструвались — просто відправляємо входити
    if not User.query.filter_by(email = data["email"]).first():
        user = User(
            email = data["email"], 
            password = data["password"]
        )
        DATABASE.session.add(user)
        DATABASE.session.commit()
    
    return flask.redirect("/auth")


def render_auth():
    
    # flask_login.current_user - объект текущего пользователя
    # flask_login.current_user.is_authenticated - запись о том, есть ли сессия у пользователя
    # is_authenticated - True/False
    
    if flask_login.current_user.is_authenticated:
        return flask.redirect("/")
    
    # flask.redirect() - меняет страницу пользователя
    
    # Полина: проверяем тип запроса, получаем почту и пароль
    if flask.request.method == "POST":
        email = flask.request.form.get("email")
        password = flask.request.form.get("password")
        
        if email and password:
            # Полина: проверяем совпадает ли почта
            user = User.query.filter_by(email = email)
            
            # Он отправляет запрос, возвращает объект пользователя
            user = user.scalar()
            
            if user:
                # Полина: проверяем правильность пароля и хешируем его
                is_correct_password = werkzeug.security.check_password_hash(
                    pwhash=user.password, 
                    password = password
                )
                
                
                if is_correct_password:
                    # Богдан: проверка пользователя
                    flask_login.login_user(user=user)
                    
                    return flask.redirect('/')
                
                else:
                    # Богдан: проверка логина и пароля
                    data = {
                        "error": "Логин или пароль неверны",
                        "email": email,
                        "password": password
                    }
                    # Богдан: **data - распаковка словаря
                    return flask.render_template("auth.html", **data)
                
            else:
                data = {
                    "error": "Такого пользователя нету",
                    "email": email,
                    "password": password
                }
                return flask.render_template("auth.html", **data)
        else:
            data = {
                "error": "Заполните все поля",
                "email": email,
                "password": password
            }
            return flask.render_template("auth.html", **data)
        
    return flask.render_template("auth.html")


# redirect - обязательный return
# render_template - обязательный return

def render_logout():
    
    # Егор Войтов: выходит из аккаунта
    flask_login.logout_user()
    
    # Егор Войтов: перенаправляет на страницу авторизации
    return flask.redirect("/auth")

# Паша
# Создать функцию отображения для шаблона opened_chat.html
# Функция принимает аргумент chat_id
def render_opened_chat(chat_id):
    
    chat = Chat.query.get(chat_id)
    
    all_chats = Chat.query.all()
    # Собрать словарь с чатом
    if chat is None:
        return flask.redirect("/")
    
    context = {
        "id": chat.id,
        "title": chat.title,
        "chats": all_chats
    }
    # Передать словарь на шаблон
    return flask.render_template("opened_chat.html", **context)
