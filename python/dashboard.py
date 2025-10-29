# python/dashboard.py
import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user
from .db import get_conn

from .auth import auth_bp, init_auth
from .reports.routes import reports_bp

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev")

# ─ Flask-Login ─
login_manager = LoginManager(app)
init_auth(login_manager)   # <- передаємо login_manager в модуль auth

# ─ Blueprints ─
app.register_blueprint(auth_bp)
app.register_blueprint(reports_bp)

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# ─ Головна ─
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
                SELECT verkaufsdatum, kunde, kundentyp, artikel, menge,
                       vk_preis, ek_preis, umsatz, kosten, marge
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

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
