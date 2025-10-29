from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import check_password_hash
from ..db import get_conn

auth_bp = Blueprint("auth", __name__)

# ── Модель користувача ──
class User(UserMixin):
    def __init__(self, id, email, name, role, is_active):
        self.id = str(id)
        self.email = email
        self.name = name
        self.role = role
        self.active = bool(is_active)

    def is_active(self):
        return self.active

# login_manager створюється в app і "під’єднується" тут через ініціалізатор
login_manager: LoginManager | None = None
login_manager.login_view = "auth.login"
login_manager.login_message = None            # вимкнути автосповіщення
# (необов'язково) login_manager.needs_refresh_message = None


def init_auth(app_login_manager: LoginManager):
    global login_manager
    login_manager = app_login_manager

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

# ── Роути ──
@auth_bp.route("/login", methods=["GET", "POST"])
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

@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Abgemeldet.", "info")
    return redirect(url_for("auth.login"))
