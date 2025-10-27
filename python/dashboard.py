# python/dashboard.py
# Dashboard (DE) + Login/Logout via Flask-Login
# Показує: Kunde, Kundentyp, Artikel, Menge, VK-Preis, EK-Preis, Umsatz, Kosten, Marge
# Додає звіт /reports/daily (Umsatz pro Tag) з фільтром дат, клієнтів і товарів

import os
from datetime import date, datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import check_password_hash
from .db import get_conn  # наша функція підключення до БД newshopdb

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev")  # секрет для сесій

# ─ Flask-Login ─
login_manager = LoginManager(app)
login_manager.login_view = "login"   # якщо не залогінена → редірект на /login


# Модель користувача (простий контейнер, не ORM)
class User(UserMixin):
    def __init__(self, id, email, name, role, is_active):
        self.id = str(id)
        self.email = email
        self.name = name
        self.role = role
        self.active = bool(is_active)

    def is_active(self):
        return self.active


# Завантаження користувача з таблиці users
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


# Додаємо current_user у всі шаблони
@app.context_processor
def inject_user():
    return dict(current_user=current_user)


# ─ Авторизація ─
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_conn()
        if conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, email, name, role, is_active, password_hash
                    FROM users
                    WHERE email=%s AND is_active=1
                """, (email,))
                row = cur.fetchone()
            conn.close()

            if row:
                uid, uemail, uname, urole, uactive, phash = row
                if check_password_hash(phash, password):
                    user = User(uid, uemail, uname, urole, uactive)
                    login_user(user)
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


# ─ Головна сторінка (останні продажі) ─
@app.get("/")
@login_required
def index():
    rows = []
    totals = {"umsatz": 0.0, "kosten": 0.0, "marge": 0.0}

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    verkaufsdatum, kunde, kundentyp, artikel,
                    menge, vk_preis, ek_preis, umsatz, kosten, marge
                FROM v_sales
                ORDER BY verkaufsdatum DESC
                LIMIT 100;
            """)
            rows = cur.fetchall()
        conn.close()

        # підсумки (просто для відображення внизу таблиці)
        if rows:
            totals["umsatz"] = float(sum(r[7] for r in rows))
            totals["kosten"] = float(sum(r[8] for r in rows))
            totals["marge"]  = float(sum(r[9] for r in rows))

    return render_template("dashboard.html", rows=rows, totals=totals, title="Dashboard")


@app.get("/dashboard")
@login_required
def dashboard_alias():
    return redirect(url_for("index"))


# ─ Звіт: Umsatz pro Tag ─
@app.get("/reports/daily")
@login_required
def report_daily():
    """
    📊 Показує звіт по днях з можливістю фільтрації:
        - за періодом дат
        - за кількома клієнтами
        - за кількома товарами
    """
    # --- 1. Зчитуємо дати з GET або задаємо дефолт ---
    bis_str = request.args.get("bis") or date.today().isoformat()
    von_str = request.args.get("von") or (date.fromisoformat(bis_str) - timedelta(days=30)).isoformat()
    von = date.fromisoformat(von_str)
    bis = date.fromisoformat(bis_str)

    # --- 2. Зчитуємо вибір клієнтів і товарів ---
    kunden_ids = [int(x) for x in request.args.getlist("kunden") if x.isdigit()]
    artikel_ids = [int(x) for x in request.args.getlist("artikel") if x.isdigit()]

    rows = []
    kunden = []
    artikel = []

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # --- 3. Завантажуємо довідники для фільтрів ---
            cur.execute("SELECT kundenID, CONCAT(vorname, ' ', nachname) FROM kunden ORDER BY nachname;")
            kunden = cur.fetchall()

            cur.execute("SELECT artikelID, produktname FROM artikel ORDER BY produktname;")
            artikel = cur.fetchall()

            # --- 4. Формуємо SQL з умовами ---
            sql = """
                SELECT
                  tag, positionen, menge, rabatt_eur, umsatz, kosten, marge,
                  umsatz_brutto, marge_brutto, marge_prozent, marge_brutto_prozent
                FROM v_sales_by_day
                WHERE tag BETWEEN %s AND %s
            """
            params = [von, bis]

            if kunden_ids:
                sql += " AND kundenID IN (" + ",".join(["%s"] * len(kunden_ids)) + ")"
                params.extend(kunden_ids)

            if artikel_ids:
                sql += " AND artikelID IN (" + ",".join(["%s"] * len(artikel_ids)) + ")"
                params.extend(artikel_ids)

            sql += " ORDER BY tag"
            cur.execute(sql, params)
            rows = cur.fetchall()
        conn.close()

    # --- 5. Підсумки ---
    totals = {
        "positionen": sum(r[1] for r in rows) if rows else 0,
        "menge": float(sum(r[2] for r in rows)) if rows else 0.0,
        "rabatt_eur": float(sum(r[3] for r in rows)) if rows else 0.0,
        "umsatz": float(sum(r[4] for r in rows)) if rows else 0.0,
        "kosten": float(sum(r[5] for r in rows)) if rows else 0.0,
        "marge": float(sum(r[6] for r in rows)) if rows else 0.0,
        "umsatz_br": float(sum(r[7] for r in rows)) if rows else 0.0,
        "marge_br": float(sum(r[8] for r in rows)) if rows else 0.0,
    }

    # --- 6. Рендер шаблону ---
    return render_template(
        "reports_daily.html",
        title="Umsatz pro Tag",
        rows=rows,
        totals=totals,
        von=von_str,
        bis=bis_str,
        kunden=kunden,
        artikel=artikel,
        sel_kunden=kunden_ids,
        sel_artikel=artikel_ids
    )


# ─ Health check ─
@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # слухаємо всі інтерфейси, щоб відкривати з ноутбука
    app.run(host="0.0.0.0", port=5000, debug=True)
