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
    # Параметри
    bis = request.args.get("bis") or date.today().isoformat()
    von = request.args.get("von") or (date.fromisoformat(bis) - timedelta(days=30)).isoformat()
    grp = request.args.get("grp", "day")  # day | month | year

    kunden_sel    = request.args.getlist("kunden")
    artikel_sel   = request.args.getlist("artikel")
    kundentyp_sel = request.args.getlist("kundentypen")

    rows = []
    totals = {}
    filter_line = ""

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # довідники (списки)
            cur.execute("SELECT kundenID, CONCAT(vorname,' ',nachname) AS kunde FROM kunden ORDER BY kunde")
            kunden_list = cur.fetchall()  # [(id, label), ...]

            cur.execute("SELECT kundentypID, bezeichnung AS typ FROM kundentyp ORDER BY typ")
            kundentyp_list = cur.fetchall()

            cur.execute("SELECT artikelID, produktname AS artikel FROM artikel ORDER BY artikel")
            artikel_list = cur.fetchall()

            # WHERE
            where_sql = "verkaufsdatum BETWEEN %s AND %s"
            params = [von, bis]

            if kunden_sel:
                where_sql += " AND kundenID IN (" + ",".join(["%s"] * len(kunden_sel)) + ")"
                params.extend(kunden_sel)
            if kundentyp_sel:
                where_sql += " AND kundentypID IN (" + ",".join(["%s"] * len(kundentyp_sel)) + ")"
                params.extend(kundentyp_sel)
            if artikel_sel:
                where_sql += " AND artikelID IN (" + ",".join(["%s"] * len(artikel_sel)) + ")"
                params.extend(artikel_sel)

            # Групування
            if grp == "month":
                label_expr = "DATE_FORMAT(verkaufsdatum, '%Y-%m')"
            elif grp == "year":
                label_expr = "DATE_FORMAT(verkaufsdatum, '%Y')"
            else:
                grp = "day"
                label_expr = "DATE(verkaufsdatum)"

            cur.execute(
                f"""
                SELECT
                  {label_expr}                        AS tag,
                  COUNT(*)                           AS positionen,
                  SUM(menge)                         AS menge,
                  ROUND(SUM(rabatt_eur), 2)          AS rabatt_eur,
                  ROUND(SUM(umsatz), 2)              AS umsatz,
                  ROUND(SUM(kosten), 2)              AS kosten,
                  ROUND(SUM(marge), 2)               AS marge,
                  ROUND(SUM(umsatz_brutto), 2)       AS umsatz_brutto,
                  ROUND(SUM(marge_brutto), 2)        AS marge_brutto,
                  ROUND(100 * SUM(marge) / NULLIF(SUM(umsatz), 0), 2)            AS marge_prozent,
                  ROUND(100 * SUM(marge_brutto) / NULLIF(SUM(umsatz_brutto), 0), 2) AS marge_brutto_prozent
                FROM v_sales
                WHERE {where_sql}
                GROUP BY {label_expr}
                ORDER BY {label_expr}
                """,
                params
            )
            rows = cur.fetchall()

        conn.close()

    # Підсумки
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
    else:
        totals = {"positionen":0,"menge":0.0,"rabatt_eur":0.0,"umsatz":0.0,"kosten":0.0,"marge":0.0,"umsatz_br":0.0,"marge_br":0.0}

    # Рядок «Gefiltert»: точні назви
    def labels_for(selected_ids, pairs):
        id_to_label = {str(pid): lbl for pid, lbl in pairs}
        names = [id_to_label.get(str(x)) for x in selected_ids if str(x) in id_to_label]
        if not names: return ""
        if len(names) <= 6:
            return ", ".join(names)
        return ", ".join(names[:6]) + f" … (+{len(names)-6})"

    kunden_txt    = labels_for(kunden_sel, kunden_list if 'kunden_list' in locals() else [])
    kundentyp_txt = labels_for(kundentyp_sel, kundentyp_list if 'kundentyp_list' in locals() else [])
    artikel_txt   = labels_for(artikel_sel, artikel_list if 'artikel_list' in locals() else [])

    parts = [f"von: {von}", f"bis: {bis}", f"Intervall: {grp}"]
    if kunden_txt:    parts.append(f"Kunde: {kunden_txt}")
    if kundentyp_txt: parts.append(f"Kundentyp: {kundentyp_txt}")
    if artikel_txt:   parts.append(f"Artikel: {artikel_txt}")
    filter_line = "Gefiltert → " + " · ".join(parts)

    return render_template(
        "reports_daily.html",
        title=f"Umsatz pro {grp}",
        rows=rows, totals=totals,
        von=von, bis=bis, grp=grp,
        kunden_list=kunden_list if 'kunden_list' in locals() else [],
        artikel_list=artikel_list if 'artikel_list' in locals() else [],
        kundentyp_list=kundentyp_list if 'kundentyp_list' in locals() else [],
        kunden_sel=kunden_sel, artikel_sel=artikel_sel, kundentyp_sel=kundentyp_sel,
        filter_line=filter_line,
    )



@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
