""" Hauptdatei der Flask-Anwendung (Startpunkt)
In dieser Datei starte ich meine Flask-Anwendung.
Ich habe mehrere Blueprints: auth für Login, reports für Berichte und dashboard für die Hauptseite.
Das Dashboard zeigt die letzten Verkäufe und berechnet Umsatz, Kosten und Marge.
Die App läuft auf Port 5000 und hat einen kleinen Healthcheck
"""

import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user

# Eigene Module importieren (Datenbank, Login, Reports)
from .db import get_conn
from .auth import auth_bp, init_auth
from .reports.routes import reports_bp
from flask import Blueprint

#  Flask-App erstellen
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev")# Geheimschlüssel (wichtig für Sitzungen und Login)

# Login-System initialisieren
login_manager = LoginManager(app)
init_auth(login_manager)

# ==========Dashboard-Blueprint definieren==========
dashboard_bp = Blueprint("dashboard", __name__)

# Startseite (Home)
@dashboard_bp.get("/")
@login_required                      # Nur für eingeloggte Benutzer
def home():
    return render_template("dashboard_home.html", title="NewShop Dashboard")

# Dashboard-Tabelle mit Verkaufsdaten
@dashboard_bp.get("/dashboard")          # Route für die Seite /dashboard
@login_required                          # Zugriff nur für eingeloggte Benutzer
def table():
    rows = []                            # Liste für Verkaufszeilen (Transaktionen)

    conn = get_conn()                    # Verbindung zur Datenbank herstellen
    if conn:
        with conn.cursor() as cur:       # Cursor öffnen, um SQL-Abfragen auszuführen
            # SQL-Abfrage: die letzten 100 Verkäufe aus der Sicht (View) v_sales
            cur.execute("""
                SELECT verkaufsdatum, kunde, kundentyp, artikel, menge,
                       vk_preis, rabatt_preis, ek_preis, umsatz, kosten, marge
                FROM v_sales
                ORDER BY verkaufsdatum DESC
                LIMIT 100
            """)
            rows = cur.fetchall()        # Ergebnisse abholen
        conn.close()                     # Verbindung schließen

    # HTML-Template rendern und Daten an die Seite übergeben
    return render_template("dashboard.html",
                           rows=rows,
                           title="Dashboard")
# ========================================


#  Healthcheck – zeigt, dass der Server läuft
@app.get("/health")
def health():
    return {"status": "ok"}  # JSON-Antwort

# Blueprints registrieren
app.register_blueprint(dashboard_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(reports_bp)

# Benutzer-Information global für Templates
@app.context_processor
def inject_user():
    # current_user steht dann automatisch in allen HTML-Templates zur Verfügung
    return dict(current_user=current_user)


# Eigener Template-Filter für Zahlenformat
@app.template_filter("thousands")
def format_thousands (value, decimals=2):
    try:
        formatted = f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", " ")
        return formatted
    except (ValueError, TypeError):
        return "k. A."   # keine Angabe → немає даних


#  App starten
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
