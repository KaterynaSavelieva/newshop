# python/dashboard.py
# Dashboard (DE) + Login/Logout via Flask-Login
# Показує: Kunde, Kundentyp, Artikel, Menge, VK-Preis, EK-Preis, Umsatz, Kosten, Marge
# Додає звіт /reports/daily (Umsatz pro Tag) з фільтром дат

import os
from datetime import date, timedelta

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import check_password_hash

from .db import get_conn  # підключення до БД newshopdb

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

# ─ Головний дашборд ─
@app.get("/")
@login_required
def index():
    """
    Використовуємо VIEW v_sales, щоб отримати:
    datum, kunde, kundentyp, artikel, menge, vk_preis, ek_preis, umsatz, kosten, marge
    """
    rows = []
    totals = {"umsatz": 0.0, "kosten": 0.0, "marge": 0.0}

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    verkaufsdatum,   -- 0
                    kunde,           -- 1
                    kundentyp,       -- 2
                    artikel,         -- 3
                    menge,           -- 4
                    vk_preis,        -- 5
                    ek_preis,        -- 6
                    umsatz,          -- 7  (нетто, після знижки)
                    kosten,          -- 8
                    marge            -- 9
                FROM v_sales
                ORDER BY verkaufsdatum DESC
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

# ─ Звіт: продажі по днях ─
@app.get("/reports/daily")
@login_required
def report_daily():
    """
    Читає агреговані дані з v_sales_by_day у діапазоні дат [von..bis].
    Якщо параметри не задані — останні 30 днів.
    """
    bis = request.args.get("bis") or date.today().isoformat()
    von = request.args.get("von") or (date.fromisoformat(bis) - timedelta(days=30)).isoformat()

    rows = []
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  tag, positionen, menge, rabatt_eur, umsatz, kosten, marge,
                  umsatz_brutto, marge_brutto, marge_prozent, marge_brutto_prozent
                FROM v_sales_by_day
                WHERE tag BETWEEN %s AND %s
                ORDER BY tag
                """,
                (von, bis)
            )
            rows = cur.fetchall()
        conn.close()

    # підсумки (для футера таблиці)
    totals = {
        "positionen": sum(r[1] for r in rows) if rows else 0,
        "menge":      float(sum(r[2] for r in rows)) if rows else 0.0,
        "rabatt_eur": float(sum(r[3] for r in rows)) if rows else 0.0,
        "umsatz":     float(sum(r[4] for r in rows)) if rows else 0.0,
        "kosten":     float(sum(r[5] for r in rows)) if rows else 0.0,
        "marge":      float(sum(r[6] for r in rows)) if rows else 0.0,
        "umsatz_br":  float(sum(r[7] for r in rows)) if rows else 0.0,
        "marge_br":   float(sum(r[8] for r in rows)) if rows else 0.0,
    }

    return render_template(
        "reports_daily.html",
        title="Umsatz pro Tag",
        rows=rows,
        totals=totals,
        von=von,
        bis=bis
    )

# ─ Health для швидкої перевірки ─
@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # слухаємо всі інтерфейси, щоб відкривати з ноутбука
    app.run(host="0.0.0.0", port=5000, debug=True)
