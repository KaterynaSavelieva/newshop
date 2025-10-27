# python/dashboard.py
# Dashboard (DE) + Login/Logout via Flask-Login
# Звіт /reports/daily з фільтрами та графіком (Umsatz=bar, Marge%=line)

import os
from datetime import date, timedelta

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import check_password_hash

from .db import get_conn  # наша функція підключення до БД newshopdb

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev")

# ─ Flask-Login ─
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Проста модель користувача (дані з БД)
class User(UserMixin):
    def __init__(self, id, email, name, role, is_active):
        self.id = str(id)
        self.email = email
        self.name = name
        self.role = role
        self.active = bool(is_active)

    def is_active(self):
        return self.active

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
                    login_user(User(uid, uemail, uname, urole, uactive))
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

# ─ Головний дашборд (простий приклад останніх операцій) ─
@app.get("/")
@login_required
def index():
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
                    umsatz,          -- 7 (нетто)
                    kosten,          -- 8
                    marge            -- 9
                FROM v_sales
                ORDER BY verkaufsdatum DESC
                LIMIT 100
                """
            )
            rows = cur.fetchall()
        conn.close()

        if rows:
            totals["umsatz"] = float(sum(r[7] for r in rows))
            totals["kosten"] = float(sum(r[8] for r in rows))
            totals["marge"]  = float(sum(r[9] for r in rows))

    return render_template("dashboard.html", rows=rows, totals=totals, title="Dashboard")

@app.get("/dashboard")
@login_required
def dashboard_alias():
    return redirect(url_for("index"))

# ─ Звіт: продажі (з фільтрами) ─
@app.get("/reports/daily")
@login_required
def report_daily():
    """
    Фільтри: період дат, кілька клієнтів, кілька артикулів, деталізація Tag/Monat/Jahr.
    ВАЖЛИВО: для DATE_FORMAT використовуємо '%%Y-%%m' (подвійні %) — інакше Python
    подумає, що це свій форматер і впаде з помилкою 'unsupported format character'.
    """
    # 1) зчитуємо фільтри з GET
    bis = request.args.get("bis") or date.today().isoformat()
    von = request.args.get("von") or (date.fromisoformat(bis) - timedelta(days=30)).isoformat()
    group = (request.args.get("group") or "tag").lower()   # tag | monat | jahr

    # мультивибір -> список int
    kunden_ids = [int(x) for x in request.args.getlist("kunden") if x.strip().isdigit()]
    artikel_ids = [int(x) for x in request.args.getlist("artikel") if x.strip().isdigit()]

    # 2) мапа для групування
    if group == "monat":
        # подвійні % у форматі !
        grp_sql = "DATE_FORMAT(verkaufsdatum, '%%Y-%%m')"
    elif group == "jahr":
        grp_sql = "YEAR(verkaufsdatum)"
    else:
        grp_sql = "DATE(verkaufsdatum)"  # tag

    rows = []
    totals = {}

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # 3) базовий WHERE + параметри
            where_sql = "verkaufsdatum BETWEEN %s AND %s"
            params = [von, bis]

            # фільтр клієнтів (id з v_sales.kundenID)
            if kunden_ids:
                placeholders = ",".join(["%s"] * len(kunden_ids))
                where_sql += f" AND kundenID IN ({placeholders})"
                params.extend(kunden_ids)

            # фільтр артикулів (id з v_sales.artikelID)
            if artikel_ids:
                placeholders = ",".join(["%s"] * len(artikel_ids))
                where_sql += f" AND artikelID IN ({placeholders})"
                params.extend(artikel_ids)

            # 4) агрегуємо з v_sales по вибраній групі
            cur.execute(
                f"""
                SELECT
                    {grp_sql}                                       AS tag,           -- мітка групи
                    COUNT(*)                                        AS positionen,    -- рядків продажу
                    SUM(menge)                                      AS menge,         -- шт
                    ROUND(SUM(rabatt_eur), 2)                       AS rabatt_eur,    -- знижка €
                    ROUND(SUM(umsatz), 2)                           AS umsatz,        -- виручка NETTO
                    ROUND(SUM(kosten), 2)                           AS kosten,        -- собівартість
                    ROUND(SUM(marge), 2)                            AS marge,         -- маржа NETTO
                    ROUND(SUM(umsatz_brutto), 2)                    AS umsatz_brutto, -- BRUTTO
                    ROUND(SUM(marge_brutto), 2)                     AS marge_brutto,  -- маржа BRUTTO
                    ROUND(100 * SUM(marge) / NULLIF(SUM(umsatz), 0), 2)        AS marge_prozent,
                    ROUND(100 * SUM(marge_brutto) / NULLIF(SUM(umsatz_brutto), 0), 2) AS marge_brutto_prozent
                FROM v_sales
                WHERE {where_sql}
                GROUP BY tag
                ORDER BY tag
                """,
                params,
            )
            rows = cur.fetchall()

            # для селектів у формі (показати опції і зберігати вибір)
            cur.execute("SELECT kundenID, CONCAT(vorname,' ',nachname) AS name FROM kunden ORDER BY name")
            kunden_list = cur.fetchall()  # [(id, name), ...]

            cur.execute("SELECT artikelID, produktname FROM artikel ORDER BY produktname")
            artikel_list = cur.fetchall()  # [(id, name), ...]

        conn.close()

        # 5) підсумки для футера
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
            # агрегований % від суми (а не середнє)
            totals["marge_pct"] = round(100.0 * totals["marge"] / totals["umsatz"], 2) if totals["umsatz"] else 0.0
            totals["marge_br_pct"] = round(100.0 * totals["marge_br"] / totals["umsatz_br"], 2) if totals["umsatz_br"] else 0.0
        else:
            totals = {k: 0 for k in ("positionen","menge","rabatt_eur","umsatz","kosten","marge","umsatz_br","marge_br")}
            totals["marge_pct"] = 0.0
            totals["marge_br_pct"] = 0.0

    # 6) рендеримо шаблон
    return render_template(
        "reports_daily.html",
        title="Umsatz pro Tag",
        rows=rows,
        totals=totals,
        von=von, bis=bis,
        group=group,
        kunden_list=kunden_list,
        artikel_list=artikel_list,
        selected_kunden=kunden_ids,
        selected_artikel=artikel_ids,
    )

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
