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

# ✅ використовуємо твої утиліти
from .reports.service import f_group_expr, f_labels_for, f_build_where_sql

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev")

# ─ Flask-Login ─
login_manager = LoginManager(app)
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
            where_sql, params = f_build_where_sql(von, bis, kunden_sel, kundentyp_sel, artikel_sel)

            # Групування єдиною функцією
            label_expr = f_group_expr(grp, "verkaufsdatum")

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

    # ✅ Рядок «Gefilterт»: використовуємо утиліту f_labels_for
    kunden_txt    = f_labels_for(kunden_sel,    kunden_list)
    kundentyp_txt = f_labels_for(kundentyp_sel, kundentyp_list)
    artikel_txt   = f_labels_for(artikel_sel,   artikel_list)

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

# ─ Звіт: Umsatz pro Kunde ─
@app.get("/reports/customers")
@login_required
def report_customers():
    from datetime import date, timedelta

    bis = request.args.get("bis") or date.today().isoformat()
    von = request.args.get("von") or (date.fromisoformat(bis) - timedelta(days=30)).isoformat()

    kunden_sel    = request.args.getlist("kunden")
    artikel_sel   = request.args.getlist("artikel")
    kundentyp_sel = request.args.getlist("kundentypen")

    # top_n
    try:
        top_n = int(request.args.get("top", "20"))
    except ValueError:
        top_n = 20
    top_n = max(5, min(top_n, 100))

    rows = []
    filter_line = ""
    totals = {}

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # довідники
            cur.execute("SELECT kundenID, CONCAT(vorname,' ',nachname) AS kunde FROM kunden ORDER BY kunde")
            kunden_list = cur.fetchall()

            cur.execute("SELECT kundentypID, bezeichnung AS typ FROM kundentyp ORDER BY typ")
            kundentyp_list = cur.fetchall()

            cur.execute("SELECT artikelID, produktname AS artikel FROM artikel ORDER BY artikel")
            artikel_list = cur.fetchall()

            # WHERE
            where_sql, params = f_build_where_sql(von, bis, kunden_sel, kundentyp_sel, artikel_sel)

            sql = f"""
                SELECT
                  kundenID,
                  kunde,
                  COUNT(*)                              AS positionen,
                  SUM(menge)                            AS menge,
                  ROUND(SUM(umsatz), 2)                 AS umsatz,
                  ROUND(SUM(kosten), 2)                 AS kosten,
                  ROUND(SUM(umsatz) - SUM(kosten), 2)   AS marge,
                  ROUND(100 * (SUM(umsatz) - SUM(kosten)) / NULLIF(SUM(umsatz), 0), 2) AS marge_prozent
                FROM v_sales
                WHERE {where_sql}
                GROUP BY kundenID, kunde
                ORDER BY umsatz DESC
                LIMIT {top_n}
            """
            cur.execute(sql, params)
            rows = cur.fetchall()

        conn.close()

    # Підсумки
    if rows:
        totals = {
            "positionen": sum(r[2] for r in rows),
            "menge":      float(sum(r[3] for r in rows)),
            "umsatz":     float(sum(r[4] for r in rows)),
            "kosten":     float(sum(r[5] for r in rows)),
            "marge":      float(sum(r[6] for r in rows)),
        }
    else:
        totals = {"positionen":0,"menge":0.0,"umsatz":0.0,"kosten":0.0,"marge":0.0}

    # ✅ Рядок “Gefiltert”
    kunden_txt    = f_labels_for(kunden_sel,    kunden_list)
    kundentyp_txt = f_labels_for(kundentyp_sel, kundentyp_list)
    artikel_txt   = f_labels_for(artikel_sel,   artikel_list)

    parts = [f"von: {von}", f"bis: {bis}", f"Top: {top_n}"]
    if kunden_txt:    parts.append(f"Kunde: {kunden_txt}")
    if kundentyp_txt: parts.append(f"Kundentyp: {kundentyp_txt}")
    if artikel_txt:   parts.append(f"Artikel: {artikel_txt}")
    filter_line = "Gefiltert → " + " · ".join(parts)

    return render_template(
        "reports_customers.html",
        title="Umsatz pro Kunde",
        rows=rows, totals=totals,
        von=von, bis=bis, top_n=top_n,
        kunden_list=kunden_list if 'kunden_list' in locals() else [],
        artikel_list=artikel_list if 'artikel_list' in locals() else [],
        kundentyp_list=kundentyp_list if 'kundentyp_list' in locals() else [],
        kunden_sel=kunden_sel, artikel_sel=artikel_sel, kundentyp_sel=kundentyp_sel,
        filter_line=filter_line,
    )

# ─ Звіт: Umsatz pro Artikel ─
@app.get("/reports/articles")
@login_required
def report_articles():
    from datetime import date, timedelta

    bis = request.args.get("bis") or date.today().isoformat()
    von = request.args.get("von") or (date.fromisoformat(bis) - timedelta(days=30)).isoformat()

    artikel_sel   = request.args.getlist("artikel")
    kunden_sel    = request.args.getlist("kunden")
    kundentyp_sel = request.args.getlist("kundentypen")
    grp = request.args.get("grp", "items")  # items | day | month | year

    try:
        top_n = int(request.args.get("top", "20"))
    except ValueError:
        top_n = 20
    top_n = max(5, min(top_n, 100))

    rows = []
    totals = {}
    filter_line = ""
    ts_mode_msg = None

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # Довідники
            cur.execute("SELECT artikelID, produktname FROM artikel ORDER BY produktname")
            artikel_list = cur.fetchall()
            cur.execute("SELECT kundenID, CONCAT(vorname,' ',nachname) FROM kunden ORDER BY 2")
            kunden_list = cur.fetchall()
            cur.execute("SELECT kundentypID, bezeichnung FROM kundentyp ORDER BY bezeichnung")
            kundentyp_list = cur.fetchall()

            # WHERE
            where_sql, params = f_build_where_sql(von, bis, kunden_sel, kundentyp_sel, artikel_sel)

            if grp == "items":
                # Top-N по артикулах
                sql = f"""
                    SELECT
                      artikelID,
                      artikel,
                      COUNT(*)              AS positionen,
                      SUM(menge)            AS menge,
                      ROUND(SUM(umsatz),2)  AS umsatz,
                      ROUND(SUM(kosten),2)  AS kosten,
                      ROUND(SUM(marge),2)   AS marge,
                      ROUND(100*SUM(marge)/NULLIF(SUM(umsatz),0),2) AS marge_prozent
                    FROM v_sales
                    WHERE {where_sql}
                    GROUP BY artikelID, artikel
                    ORDER BY umsatz DESC
                    LIMIT {top_n}
                """
                cur.execute(sql, params)
                rows = cur.fetchall()

            else:
                # часовий ряд для 1 артикула
                if len(artikel_sel) != 1:
                    ts_mode_msg = "Bitte genau einen Artikel wählen, um einen Zeitverlauf anzuzeigen."
                else:
                    label_expr = f_group_expr(grp, "verkaufsdatum")

                    sql = f"""
                        SELECT
                          {label_expr}                       AS label,
                          COUNT(*)                           AS positionen,
                          SUM(menge)                         AS menge,
                          ROUND(SUM(umsatz),2)               AS umsatz,
                          ROUND(SUM(kosten),2)               AS kosten,
                          ROUND(SUM(marge),2)                AS marge,
                          ROUND(100*SUM(marge)/NULLIF(SUM(umsatz),0),2) AS marge_prozent
                        FROM v_sales
                        WHERE {where_sql}
                          AND artikelID = %s
                        GROUP BY label
                        ORDER BY label
                    """
                    params_ts = params + [artikel_sel[0]]
                    cur.execute(sql, params_ts)
                    rows = cur.fetchall()

        conn.close()

    if rows:
        pos_idx   = 2 if grp == "items" else 1
        menge_idx = 3 if grp == "items" else 2
        umsatz_idx= 4 if grp == "items" else 3
        kosten_idx= 5 if grp == "items" else 4
        marge_idx = 6 if grp == "items" else 5

        totals = {
            "positionen": sum(r[pos_idx] for r in rows),
            "menge":      float(sum(r[menge_idx] for r in rows)),
            "umsatz":     float(sum(r[umsatz_idx] for r in rows)),
            "kosten":     float(sum(r[kosten_idx] for r in rows)),
            "marge":      float(sum(r[marge_idx]  for r in rows)),
        }
    else:
        totals = {"positionen":0,"menge":0.0,"umsatz":0.0,"kosten":0.0,"marge":0.0}

    # ✅ Рядок фільтра
    artikel_txt   = f_labels_for(artikel_sel,   artikel_list)
    kunden_txt    = f_labels_for(kunden_sel,    kunden_list)
    kundentyp_txt = f_labels_for(kundentyp_sel, kundentyp_list)

    parts=[f"von: {von}", f"bis: {bis}", f"Modus: {'Artikel' if grp=='items' else grp}"]
    if artikel_txt:   parts.append(f"Artikel: {artikel_txt}")
    if kunden_txt:    parts.append(f"Kunde: {kunden_txt}")
    if kundentyp_txt: parts.append(f"Kundentyp: {kundentyp_txt}")
    filter_line="Gefiltert → "+" · ".join(parts)

    return render_template(
        "reports_articles.html",
        title="Umsatz pro Artikel",
        rows=rows, totals=totals,
        von=von, bis=bis, top_n=top_n, grp=grp,
        artikel_list=artikel_list if 'artikel_list' in locals() else [],
        kunden_list=kunden_list if 'kunden_list' in locals() else [],
        kundentyp_list=kundentyp_list if 'kundentyp_list' in locals() else [],
        artikel_sel=artikel_sel, kunden_sel=kunden_sel, kundentyp_sel=kundentyp_sel,
        filter_line=filter_line, ts_mode_msg=ts_mode_msg,
    )

@app.get("/reports/stock_low")
@login_required
def report_stock_low():
    threshold = request.args.get("limit", "150")
    try:
        threshold = int(threshold)
    except ValueError:
        threshold = 150

    rows = []
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  artikelID,
                  produktname AS artikel,
                  lagerbestand,
                  %s AS schwelle,
                  lagerbestand - %s AS differenz
                FROM artikel
                WHERE lagerbestand < %s
                ORDER BY lagerbestand ASC
                """,
                (threshold, threshold, threshold)
            )
            rows = cur.fetchall()
        conn.close()

    return render_template(
        "reports_stock_low.html",
        title="Lagerwarnung / Artikel mit niedrigem Bestand",
        rows=rows, threshold=threshold
    )

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
