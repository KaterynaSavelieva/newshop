"""
Dieses Modul verbindet sich mit der MySQL-Datenbank.
Die Zugangsdaten (Host, Port, Benutzername, Passwort)
werden aus der .env-Datei geladen.
Die Funktion get_conn() probiert mehrere Host-Port-Kombinationen,
bis eine Verbindung erfolgreich ist.
Mit fetch_one und fetch_all kann man einfach SQL-Abfragen ausführen.
"""

import os
import pymysql
from pymysql.cursors import Cursor
from dotenv import load_dotenv
from pathlib import Path

# 🔹 .env-Datei laden (liegt im Hauptordner newshop)
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)
for var in ["DB_HOSTS", "DB_PORTS", "DB_USER", "DB_PASSWORD", "DB_NAME"]:
    if not os.getenv(var):
        print(f"⚠️  Warnung: {var} ist nicht gesetzt!")



def get_conn():
    """
    Verbindung zur Datenbank herstellen.
    Mehrere Hosts und Ports werden ausprobiert.
    """

    # Hosts und Ports aus .env lesen (mit Standardwerten)
    hosts = [h.strip() for h in os.getenv("DB_HOSTS").split(",")]
    ports = [int(p.strip()) for p in os.getenv("DB_PORTS").split(",")]

    # Zugangsdaten und Datenbankname
    user = os.getenv("DB_USER")
    pwd  = os.getenv("DB_PASSWORD")
    db   = os.getenv("DB_NAME")

    # Debug-Ausgabe zur Kontrolle
    print("TRY:", hosts, ports, user, f"pwd_len={len(pwd)}", f"pwd_repr={repr(pwd)}")

    last_err = None

    # Jede Kombination aus Host und Port testen
    for host in hosts:
        for port in ports:
            try:
                # Verbindung aufbauen
                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=pwd,
                    database=db,
                    charset="utf8mb4",
                    autocommit=False,
                    cursorclass=Cursor,
                    connect_timeout=4
                )
                print(f"Verbindung erfolgreich: {host}:{port}")
                return conn
            except Exception as e:
                # Fehler merken und weiter versuchen
                print(f"Verbindung fehlgeschlagen {host}:{port} → {e}")
                last_err = e

    # Keine Verbindung möglich
    print("Keine Verbindung zum Server.")
    if last_err:
        print(f"Letzter Fehler: {last_err}")
    return None


def fetch_one(cur, sql, params=None):
    """Ein Datensatz zurückgeben (oder None)."""
    cur.execute(sql, params or ())
    return cur.fetchone()


def fetch_all(cur, sql, params=None):
    """Alle Datensätze zurückgeben (als Liste)."""
    cur.execute(sql, params or ())
    return cur.fetchall()


if __name__ == "__main__":
    # Test der Verbindung
    conn = get_conn()
    if conn:
        print("Datenbank verfügbar!")
        conn.close()
    else:
        print("Keine Verbindung.")
