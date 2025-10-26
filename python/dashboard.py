# python/dashboard.py
# Дашборд (DE) + повний логін/логаут через Flask-Login

import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import check_password_hash
from db import get_conn  # наша функція підключення до БД newshopdb

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev")  # секрет для сесій

# ─ Flask-Login ─
login_manager = LoginManager(app)
login_manager.login_view = "login"   # куди редіректити, якщо не залогінений

# Модель-контейнер (не ORM). Дані беремо з БД.
class User(UserMixin):
    def __init__(self, id, email, name, role, is_active):
        self.id = str(id)
        self.email = email
        self.name = name
        self.role = role
        self.active = bool(is_active)

    def is_active(self):
        return self.active

# завантаження користувача за id (для сесій)
@login_manager.user_loader
def load_user(user_id: str):
    conn = get_conn()
    if not conn:
        return None
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, email, name, role, is_active FROM users WHERE id=%s",
            (user_id,)
        )
        row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return User(*row)

# робимо current_user доступним у всіх шаблонах
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# ─ Маршрути авторизації ─
@app.route("/login", methods=["GET", "POST"])
def login():
    # якщо вже залогінена — на дашборд
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, email, name, role, is_active, password_hash
                    FROM users
                    WHERE email=%s AND is_active=1
                    """,
                    (email,)
                )
                row = cur.fetchone()
            conn.close()

            if row:
                uid, uemail, uname, urole, uactive, phash = row
                if check_password_hash(phash, password):
                    user = User(uid, uemail, uname, urole, uactive)
                    login_user(user)          # створюємо сесію
                    flash("Erfolgreich eingeloggt.", "success")
                    return redirect(url_for("index"))
                else:
                    error = "Falsches Passwort."
            else:
                error = "Unbekannte E-Mail oder Konto ist deaktiviert."
        else:
            error = "Datenbankverbindung fehlgeschlagen."

    return render_template("login.html", title="Anmelden", error=error)

@app.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Abgemeldet.", "info")
    return redirect(url_for("login"))

# ─ Дашборд ─
@app.get("/")
@login_required
def index():
    rows = []
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT v.verkaufsdatum, a.produktname, va.verkaufsmenge, va.verkaufspreis
                FROM verkauf v
                JOIN verkaufartikel va ON v.verkaufID = va.verkaufID
                JOIN artikel a         ON a.artikelID = va.artikelID
                ORDER BY v.verkaufsdatum DESC
                LIMIT 20;
                """
            )
            rows = cur.fetchall()
        conn.close()

    return render_template("dashboard.html", rows=rows, title="Dashboard")

# ─ Health для швидкої перевірки ─
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # слухаємо всі інтерфейси, щоб відкривати з ноутбука
    app.run(host="0.0.0.0", port=5000, debug=True)
