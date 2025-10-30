# newshop/python/auth/routes.py
from urllib.parse import urlparse, urljoin

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, UserMixin, current_user
)
from werkzeug.routing import BuildError
from werkzeug.security import check_password_hash

from ..db import get_conn


auth_bp = Blueprint("auth", __name__)


# -------- User model (спільна для load_user і login) --------
class User(UserMixin):
    def __init__(self, uid, email, name, role, is_active):
        self.id = str(uid)         # Flask-Login очікує рядок
        self.email = email
        self.name = name
        self.role = role
        self._active = bool(is_active)

    @property
    def is_active(self):
        return self._active


# -------- Ініціалізація Flask-Login --------
def init_auth(login_manager: LoginManager):
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

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


# -------- Допоміжні функції редіректу після логіну --------
def _is_safe_url(target: str) -> bool:
    if not target:
        return False
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc


def _after_login_url() -> str:
    # 1) якщо був next і він безпечний — туди
    nxt = request.args.get("next") or request.form.get("next")
    if _is_safe_url(nxt):
        return nxt

    # 2) твої основні ендпоінти по пріоритету
    for ep in ("dashboard.home", "reports.daily", "dashboard.index"):
        try:
            return url_for(ep)
        except BuildError:
            continue

    # 3) запасний варіант
    return "/"


# -------- Роути авторизації --------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_after_login_url())

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
                if phash and check_password_hash(phash, password):
                    login_user(User(uid, uemail, uname, urole, uactive))
                    flash("Erfolgreich eingeloggt.", "success")
                    return redirect(_after_login_url())
                else:
                    error = "Falsches Passwort."
            else:
                error = "Unbekannte E-Mail oder Konto ist deaktiviert."
        else:
            error = "Datenbankverbindung fehlgeschlagen."

    return render_template("login.html", title="Anmelden", error=error)


@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Abgemeldet.", "info")
    return redirect(url_for("auth.login"))
