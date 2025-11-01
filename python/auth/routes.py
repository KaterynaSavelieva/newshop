""" Autorisierungsmodul (Login / Logout)
In dieser Datei habe ich das Login-System implementiert.
Es gibt ein Blueprint namens auth.
Hier kann sich der Benutzer anmelden oder abmelden.
Die Funktion init_auth() verbindet Flask-Login mit unserer Datenbank.
Wenn der Benutzer eingeloggt ist, merkt sich Flask seine ID in einer Session.
Beim Logout wird diese Session beendet.
"""

# Hilfsfunktionen für URLs (z. B. um sichere Weiterleitungen zu prüfen)
from urllib.parse import urlparse, urljoin

# Flask-Basismodule für Webseiten, Weiterleitungen und Formulare
from flask import Blueprint, render_template, redirect, url_for, flash, request

# Flask-Login – Modul für Benutzer-Anmeldung (Session-Verwaltung)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, UserMixin, current_user)

# Werkzeug – internes Flask-Modul für Fehlerbehandlung und Passwortprüfung
from werkzeug.routing import BuildError
from werkzeug.security import check_password_hash

# Verbindung zur Datenbank (eigene Hilfsfunktion aus db.py)
from ..db import get_conn


#  1) Blueprint – das ist eine „Unter-App“ in Flask.
#     Damit können Login-Seiten getrennt vom Hauptprogramm organisiert werden.
auth_bp = Blueprint("auth", __name__)


#  2) User-Klasse für Flask-Login
# Diese Klasse beschreibt einen Benutzer (User).
# Sie wird sowohl beim Einloggen als auch beim Laden aus der Datenbank verwendet.
class User(UserMixin):
    def __init__(self, uid, email, name, role, is_active):
        self.id = str(uid)         # Flask-Login erwartet die ID als Text (string)
        self.email = email
        self.name = name
        self.role = role
        self._active = bool(is_active)

    @property
    def is_active(self):
        return self._active   # gibt zurück, ob das Konto aktiv ist (True/False)


#  3) Initialisierung von Flask-Login
# Diese Funktion wird in app.py aufgerufen:
#    init_auth(login_manager)
# Sie erklärt Flask-Login, wie ein Benutzer geladen wird.
def init_auth(login_manager: LoginManager):
    login_manager.login_view = "auth.login"              # Seite zum Einloggen
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # Diese innere Funktion wird immer aufgerufen, wenn Flask wissen will,
    # wer aktuell eingeloggt ist.
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
        return User(*row)   # erstellt ein User-Objekt aus den Datenbankwerten


#  4) Hilfsfunktionen für sichere Weiterleitungen (redirect nach Login)
def _is_safe_url(target: str) -> bool:
    # prüft, ob der Link zur gleichen Website gehört (nicht extern)
    if not target:
        return False
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc


def _after_login_url() -> str:
    # 1️ Wenn "next" vorhanden ist (z. B. vom Login-Formular) → dorthin gehen
    nxt = request.args.get("next") or request.form.get("next")
    if _is_safe_url(nxt):
        return nxt

    # 2 Sonst gehe zu einer der Hauptseiten (Dashboard, Reports, ...)
    for ep in ("dashboard.home", "reports.daily", "dashboard.index"):
        try:
            return url_for(ep)
        except BuildError:
            continue

    # 3️ Fallback – falls nichts gefunden wurde
    return "/"


#  5) Login-Seite (GET/POST)
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Wenn der Benutzer bereits eingeloggt ist → weiterleiten
    if current_user.is_authenticated:
        return redirect(_after_login_url())

    error = None

    if request.method == "POST":
        # Daten aus dem Formular lesen
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Verbindung zur Datenbank
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

            # Wenn Benutzer existiert:
            if row:
                uid, uemail, uname, urole, uactive, phash = row
                # Passwort prüfen
                if phash and check_password_hash(phash, password):
                    # Benutzer anmelden (Session starten)
                    login_user(User(uid, uemail, uname, urole, uactive))
                    flash("Erfolgreich eingeloggt.", "success")
                    return redirect(_after_login_url())
                else:
                    error = "Falsches Passwort."
            else:
                error = "Unbekannte E-Mail oder Konto ist deaktiviert."
        else:
            error = "Datenbankverbindung fehlgeschlagen."

    # Wenn GET oder Fehler → Seite mit Fehlermeldung anzeigen
    return render_template("login.html", title="Anmelden", error=error)


#  6) Logout-Route
@auth_bp.get("/logout")
@login_required   # darf nur aufgerufen werden, wenn jemand eingeloggt ist
def logout():
    logout_user()  # beendet die Session
    flash("Abgemeldet.", "info")
    return redirect(url_for("auth.login"))   # zurück zur Login-Seite
