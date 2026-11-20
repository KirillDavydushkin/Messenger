import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

import dotenv
import flask
import itsdangerous

from app.settings import main_app

# Куди лежить ілюстрація для листа
EMAIL_ART_PATH = os.path.join(
    os.path.dirname(__file__), "static", "media", "email_art.jpg"
)

EMAIL_SUBJECT = "Перевірка пошти"
TOKEN_SALT = "email-confirm"
TOKEN_MAX_AGE = 60 * 60 * 24  # посилання діє 24 години


def _serializer():
    # Підписуємо дані тим самим secret_key, що й сесії flask_login
    return itsdangerous.URLSafeTimedSerializer(
        main_app.secret_key, salt=TOKEN_SALT
    )


def make_token(email, password_hash):
    # У токені лежать пошта і ХЕШ пароля, тому користувач
    # з'являється в базі тільки після підтвердження пошти
    return _serializer().dumps({"email": email, "password": password_hash})


def read_token(token):
    # Повертає словник з даними або None, якщо токен зіпсований / прострочений
    try:
        return _serializer().loads(token, max_age=TOKEN_MAX_AGE)
    except itsdangerous.BadData:
        return None


def send_confirmation_email(to_email, confirm_url):
    """Збирає лист як на макеті та відправляє його через SMTP."""
    dotenv.load_dotenv()

    host = os.getenv("MAIL_HOST", "smtp.gmail.com")
    port = int(os.getenv("MAIL_PORT", "465"))
    user = os.getenv("MAIL_USER")
    password = os.getenv("MAIL_PASSWORD")
    sender_name = os.getenv("MAIL_SENDER_NAME", "World IT")
    sender_email = os.getenv("MAIL_FROM", user)

    if not user or not password:
        raise RuntimeError("У .env не вказані MAIL_USER та MAIL_PASSWORD")

    html = flask.render_template(
        "email/confirm_email.html", confirm_url=confirm_url
    )
    text = (
        "Вас вітає команда World IT!\n\n"
        "Щоб завершити реєстрацію та переконатися, що саме ви є власником "
        "цієї електронної адреси, будь ласка, підтвердьте свою пошту:\n"
        f"{confirm_url}\n\n"
        "Якщо у вас виникнуть питання — ми завжди раді допомогти!\n"
        "З найкращими побажаннями, команда World IT Academy"
    )

    message = EmailMessage()
    message["Subject"] = EMAIL_SUBJECT
    message["From"] = formataddr((sender_name, sender_email))
    message["To"] = to_email
    message.set_content(text)
    message.add_alternative(html, subtype="html")

    # Ілюстрація вбудовується в лист (cid:email_art), а не підтягується з сайту
    with open(EMAIL_ART_PATH, "rb") as art:
        message.get_payload()[1].add_related(
            art.read(), maintype="image", subtype="jpeg", cid="<email_art>"
        )

    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as smtp:
            smtp.login(user, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(user, password)
            smtp.send_message(message)
