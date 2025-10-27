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

# ─ Звіт: продажі по днях з фільтрами дат + кілька клієнтів + кілька товарів ─
# --- ЗАМІНИ МАРШРУТ /reports/daily ЦИМ ВАРІАНТОМ ---

from datetime import date, timedelta
from flask import request, render_template
from .db import get_conn

@app.get("/reports/daily")
@login_required
def report_daily():
    """
    Звіт 'Umsatz pro Tag' з фільтрами:
    - період дат (von..bis)
    - мультивибір клієнтів/артикулів
    - деталізація: Tag / Monat / Jahr
    Дані беремо з v_sales (detail), фільтруємо й агрегуємо на льоту.
    """

    # 1) читаємо параметри або ставимо дефолт
    bis = request.args.get("bis") or date.today().isoformat()
    von = request.args.get("von") or (date.fromisoformat(bis) - timedelta(days=30)).isoformat()
    group = request.args.get("group") or "tag"   # 'tag' | 'monat' | 'jahr'

    # 2) мультивибір (списки id як інти)
    kunden_ids = [int(x) for x in request.args.getlist("kunden") if x.strip().isdigit()]
    artikel_ids = [int(x) for x in request.args.getlist("artikel") if x.strip().isdigit()]

    # 3) конструюємо WHERE (фільтри)
    where_sql = ["verkaufsdatum BETWEEN %s AND %s"]
    params = [von, bis]

    if kunden_ids:
        where_sql.append("kundenID IN (" + ",".join(["%s"] * len(kunden_ids)) + ")")
        params.extend(kunden_ids)

    if artikel_ids:
        where_sql.append("artikelID IN (" + ",".join(["%s"] * len(artikel_ids)) + ")")
        params.extend(artikel_ids)

    where_sql = " WHERE " + " AND ".join(where_sql)

    # 4) вибираємо ключ групування
    #    (щоб не лізти в VIEW — просто формат дати міняємо у SELECT)
    if group == "monat":
        # YYYY-MM для місяців
        tag_expr = "DATE_FORMAT(verkaufsdatum, '%Y-%m')"
        order_expr = "DATE_FORMAT(verkaufsdatum, '%Y-%m')"
    elif group == "jahr":
        # YYYY для років
        tag_expr = "DATE_FORMAT(verkaufsdatum, '%Y')"
        order_expr = "DATE_FORMAT(verkaufsdatum, '%Y')"
    else:
        # за днями (за замовчуванням)
        tag_expr = "DATE(verkaufsdatum)"
        order_expr = "DATE(verkaufsdatum)"

    rows = []
    kunden_list = []
    artikel_list = []

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:

            # 5) Агрегація (нетто/брутто, кількість, маржа…)
            cur.execute(
                f"""
                SELECT
                    {tag_expr}                                   AS tag,          -- день/місяць/рік
                    COUNT(*)                                     AS positionen,   -- рядків продажу
                    SUM(menge)                                   AS menge,
                    ROUND(SUM(rabatt_eur), 2)                    AS rabatt_eur,
                    ROUND(SUM(umsatz), 2)                        AS umsatz,       -- нетто (зі знижкою)
                    ROUND(SUM(kosten), 2)                        AS kosten,
                    ROUND(SUM(marge), 2)                         AS marge,        -- нетто
                    ROUND(SUM(umsatz_brutto), 2)                 AS umsatz_brutto,
                    ROUND(SUM(marge_brutto), 2)                  AS marge_brutto,
                    ROUND(100 * SUM(marge)        / NULLIF(SUM(umsatz), 0), 2)    AS marge_prozent,
                    ROUND(100 * SUM(marge_brutto) / NULLIF(SUM(umsatz_brutto), 0), 2) AS marge_brutto_prozent
                FROM v_sales
                {where_sql}
                GROUP BY {order_expr}
                ORDER BY {order_expr}
                """,
                params
            )
            rows = cur.fetchall()

            # 6) Довідники для селектів у формі
            cur.execute("SELECT kundenID, CONCAT(vorname,' ',nachname) FROM kunden ORDER BY nachname, vorname")
            kunden_list = cur.fetchall()       # [(id, name), ...]

            cur.execute("SELECT artikelID, produktname FROM artikel ORDER BY produktname")
            artikel_list = cur.fetchall()      # [(id, name), ...]

        conn.close()

    # 7) Підсумки (для футера) + дві відсоткові маржі по формулах від сум
    totals = {}
    if rows:
        totals = {
            "positionen": sum(r[1] for r in rows),
            "menge":      float(sum(r[2] for r in rows)),
            "rabatt_eur": float(sum(r[3] for r in rows)),
            "umsatz":     float(sum(r[4] for r in rows)),
            "kosten":     float(sum(r[5] for r in rows)),
            "marge":      float(sum(r[6] for r in rows)),
            "umsatz_br":  float(sum(r[7] for r in rows)),
            "marge_br":   float(sum(r[8] for r in rows)),
        }
        # ► Вимога 3: відсотки як ділення підсумкових сум
        totals["marge_pct"]     = round(100 * totals["marge"]    / totals["umsatz"],    2) if totals["umsatz"] else 0.0
        totals["marge_br_pct"]  = round(100 * totals["marge_br"] / totals["umsatz_br"], 2) if totals["umsatz_br"] else 0.0
    else:
        totals = {"positionen": 0, "menge": 0.0, "rabatt_eur": 0.0,
                  "umsatz": 0.0, "kosten": 0.0, "marge": 0.0,
                  "umsatz_br": 0.0, "marge_br": 0.0,
                  "marge_pct": 0.0, "marge_br_pct": 0.0}

    # 8) Для зручності — що користувач вибрав (щоб залишалось у формі)
    selected_kunden = set(kunden_ids)
    selected_artikel = set(artikel_ids)

    return render_template(
        "reports_daily.html",
        title=(
            "Umsatz pro Tag" if group == "tag"
            else "Umsatz pro Monat" if group == "monat"
            else "Umsatz pro Jahr"
        ),
        rows=rows,
        totals=totals,
        von=von,
        bis=bis,
        group=group,
        kunden_list=kunden_list,
        artikel_list=artikel_list,
        selected_kunden=selected_kunden,
        selected_artikel=selected_artikel
    )


# ─ Health check ─
@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    # слухаємо всі інтерфейси, щоб відкривати з ноутбука
    app.run(host="0.0.0.0", port=5000, debug=True)
