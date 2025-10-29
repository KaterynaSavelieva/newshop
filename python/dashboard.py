# python/dashboard.py
import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user

from .db import get_conn
from .auth import auth_bp, init_auth
from .reports.routes import reports_bp

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev")

# ---- Flask-Login ----
login_manager = LoginManager(app)
init_auth(login_manager)

# ---- Dashboard blueprint (визначаємо тут, без імпорту самого себе) ----
from flask import Blueprint
dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.get("/")
@login_required
def home():
    """Головна сторінка NewShop Dashboard (картинка + назва магазину)"""
    return render_template("dashboard_home.html", title="NewShop Dashboard")

# Якщо хочеш мати ще й /dashboard як синонім головної:
@app.get("/dashboard")
@login_required
def dashboard_alias():
    return redirect(url_for("dashboard.home"))

# Технічний статус
@app.get("/health")
def health():
    return {"status": "ok"}

# ---- Реєстрація blueprints (ВАЖЛИВО: спочатку dashboard, потім інші) ----
app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(reports_bp)

# Щоб `current_user` був доступний у шаблонах
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
