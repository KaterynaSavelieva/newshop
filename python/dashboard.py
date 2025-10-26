# python/dashboard.py
# Dashboard (DE) + Login/Logout via Flask-Login
# Показує: Kunde, Kundentyp, Artikel, Menge, VK-Preis, EK-Preis, Umsatz, Kosten, Marge

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
login_manager.login_view = "login"   # якщо не залогінена → редірект на /login

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
    totals = {"umsatz": 0.0, "kosten": 0.0, "marge": 0.0}

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # головний звіт: продажі + клієнт + тип клієнта + собівартість + маржа
            cur.execute(
                """
                SELECT
                    v.verkaufsdatum,                                       -- 0 дата продажу
                    CONCAT(k.vorname, ' ', k.nachname)   AS kunde,          -- 1 клієнт (ПІБ)
                    kt.bezeichnung                      AS kundentyp,       -- 2 тип клієнта
                    a.produktname                       AS artikel,         -- 3 товар
                    va.verkaufsmenge                    AS menge,           -- 4 кількість
                    va.verkaufspreis                    AS vk_preis,        -- 5 ціна продажу (за од.)
                    COALESCE(a.durchschnittskosten,0)   AS ek_preis,        -- 6 собівартість (за од.)
                    (va.verkaufsmenge * va.verkaufspreis)                         AS umsatz,  -- 7 виручка
                    (va.verkaufsmenge * COALESCE(a.durchschnittskosten,0))        AS kosten,  -- 8 витрати
                    (va.verkaufsmenge * (va.verkaufspreis - COALESCE(a.durchschnittskosten,0))) AS marge  -- 9 маржа
                FROM verkauf v
                JOIN verkaufartikel va ON v.verkaufID = va.verkaufID
                JOIN artikel a         ON a.artikelID = va.artikelID
                JOIN kunden k          ON k.kundenID  = v.kundenID
                JOIN kundentyp kt      ON kt.kundentypID = k.kundentypID
                ORDER BY v.verkaufsdatum DESC
                LIMIT 100;
                """
            )
            rows = cur.fetchall()
        conn.close()

        # підсумки по вибірці
        if rows:
            totals["umsatz"] = float(sum(r[7] for r in rows))
            totals["kosten"] = float(sum(r[8] for r in rows))
            totals["marge"]  = float(sum(r[9] for r in rows))

    # у шаблон віддаємо rows (рядки таблиці) і totals (підсумки)
    return render_template("dashboard.html", rows=rows, totals=totals, title="Dashboard")

# Дружній маршрут /dashboard (на всяк випадок)
@app.get("/dashboard")
@login_required
def dashboard_alias():
    return redirect(url_for("index"))

# ─ Health для швидкої перевірки ─
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # слухаємо всі інтерфейси, щоб відкривати з ноутбука
    app.run(host="0.0.0.0", port=5000, debug=True)
