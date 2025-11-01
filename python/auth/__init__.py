""" Dieses Modul verbindet und exportiert Objekte aus der Datei routes.py.
Es gehört zum Authentifizierungs-Teil (Login, Logout, Registrierung).
Diese Datei sagt Python: „Wenn jemand mein Auth-Modul importiert,
sollen nur auth_bp und init_auth sichtbar sein.“
"""

# Importiert aus der Datei routes.py:
# - auth_bp: das "Blueprint"-Objekt (enthält alle Routen für Login usw.)
# - init_auth: eine Funktion, um das Authentifizierungssystem zu initialisieren
from .routes import auth_bp, init_auth

# __all__ gibt an, welche Namen exportiert werden dürfen,
# wenn man "from auth import *" benutzt.
# Nur diese beiden Elemente sind dann sichtbar.
__all__ = ["auth_bp", "init_auth"]
