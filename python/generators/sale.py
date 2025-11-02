# sale.py – Skript zum Erzeugen von zufälligen Verkäufen (Demo)
#
# Idee:
#  - Wähle einen zufälligen Kunden.
#  - Erstelle einen neuen Verkauf (verkauf).
#  - Füge Artikel mit zufälliger Menge hinzu.
#  - Speichere alles in der Datenbank.
#
# Dieses Skript nutzt die Tabellen:
# kunden, kundentyp, verkauf, verkaufartikel, artikel, artikelpreis.

import random
from datetime import datetime
from db import get_conn



# Hilfsfunktionen (werden von main() benutzt)
def ranges_for_type(kundentyp: str):
    """
    Gibt zwei Werte zurück:
      1) (min_menge, max_menge) – wie viele Stück von einem Artikel
      2) (min_items, max_items) – wie viele verschiedene Artikel im Verkauf
    Je nach Kundentyp (Standard, Silber, Gold, Platin)
    """
    t = (kundentyp or "Standard").strip().lower()
    if t == "standard":
        return (1, 25), (1, 25)
    if t == "silber":
        return (1, 50), (1, 50)
    if t == "gold":
        return (5, 100), (5, 100)
    if t == "platin":
        return (10, 200), (10, 200)
    return (1, 25), (1, 25)  # Standard-Werte


def pick_customer(cur):
    """
    Wählt einen zufälligen Kunden aus der Tabelle 'kunden'.
    Gibt zurück: (kundenID, Rabatt-Prozent, Kundentyp-Name)
    """
    cur.execute("""
        SELECT k.kundenID,
               COALESCE(t.kundenrabatt, 0) AS rabatt,
               COALESCE(t.bezeichnung, 'Standard') AS typ
        FROM kunden k
        LEFT JOIN kundentyp t ON t.kundentypID = k.kundentypID
        ORDER BY RAND()
        LIMIT 1;
    """)
    row = cur.fetchone()
    if not row:
        raise RuntimeError("Keine Kunden in der Tabelle 'kunden'.")
    return row[0], float(row[1]), str(row[2])


def create_sale_header(cur, kunden_id, when=None):
    """
    Erstellt einen neuen Verkauf (verkauf).
    Gibt zurück: (verkaufID, Datum)
    """
    when = when or datetime.now()
    cur.execute(
        "INSERT INTO verkauf(kundenID, verkaufsdatum) VALUES(%s, %s);",
        (kunden_id, when),
    )
    return cur.lastrowid, when


def pick_articles_with_stock(cur, max_items=5):
    """
    Wählt zufällige Artikel aus, die auf Lager sind.
    Gibt zurück: [(artikelID, lagerbestand), ...]
    """
    cur.execute("""
        SELECT artikelID, lagerbestand
        FROM artikel
        WHERE lagerbestand > 0
        ORDER BY RAND()
        LIMIT %s;
    """, (max_items,))
    return cur.fetchall()


def get_listenpreis(cur, artikel_id, when):
    """
    Holt den gültigen Preis (listenpreis) für ein Datum.
    Wenn kein Preis gefunden wird → Fehler.
    """
    cur.execute("""
        SELECT listenpreis
        FROM artikelpreis
        WHERE artikelID = %s
          AND gueltig_ab <= %s
          AND (gueltig_bis IS NULL OR gueltig_bis >= %s)
        ORDER BY gueltig_ab DESC
        LIMIT 1;
    """, (artikel_id, when, when))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Kein Preis für Artikel {artikel_id} am Datum {when}.")
    return float(row[0])


def add_sale_items(cur, verkauf_id, items, when, rabatt_pct, menge_range):
    """
    Fügt Artikel zum Verkauf hinzu.

    items = Liste von (artikelID, lagerbestand)
    menge_range = (min_menge, max_menge)
    rabatt_pct = Rabatt des Kunden (%)

    Gibt zurück: (Anzahl Artikel, Gesamtsumme ohne Rabatt)
    """
    added = 0
    total = 0.0
    min_m, max_m = menge_range

    for artikel_id, stock in items:
        if stock <= 0:
            continue  # nichts auf Lager

        # zufällige Menge – aber nicht mehr als Lagerbestand
        menge = random.randint(min_m, max_m)
        menge = min(menge, stock)
        if menge <= 0:
            continue

        preis = get_listenpreis(cur, artikel_id, when)

        # Eintrag in verkaufartikel
        cur.execute("""
            INSERT INTO verkaufartikel(verkaufID, artikelID, verkaufsmenge, verkaufspreis, rabatt)
            VALUES (%s, %s, %s, %s, %s);
        """, (verkauf_id, artikel_id, menge, preis, rabatt_pct))

        added += 1
        total += preis * menge

    return added, round(total, 2)



# Hauptprogramm
def main():
    # Verbindung zur Datenbank öffnen
    conn = get_conn()
    if not conn:
        print(" Keine Verbindung zur Datenbank.")
        return

    try:
        with conn.cursor() as cur:
            # 1) Zufälligen Kunden wählen
            kunden_id, rabatt_pct, kundentyp = pick_customer(cur)

            # 2) Wertebereiche für diesen Kundentyp
            menge_range, items_range = ranges_for_type(kundentyp)

            # 3) Verkauf-Kopf (Header) erstellen
            verkauf_id, when = create_sale_header(cur, kunden_id)

            # 4) Wie viele verschiedene Artikel soll der Kunde kaufen?
            max_items = random.randint(*items_range)

            # 5) Artikel aus dem Lager holen
            candidates = pick_articles_with_stock(cur, max_items=max_items)
            if not candidates:
                raise RuntimeError("Keine Artikel mit Lagerbestand > 0 gefunden.")

            # 6) Artikel hinzufügen
            added, total = add_sale_items(cur, verkauf_id, candidates, when, rabatt_pct, menge_range)
            if added == 0:
                raise RuntimeError("Keine Artikel hinzugefügt. Abbruch.")

        # 7) Alles speichern (commit)
        conn.commit()
        print(
            f"Verkauf erstellt: ID={verkauf_id}, Positionen={added}, "
            f"Summe (ohne Rabatt)={total:.2f}, Rabatt={rabatt_pct:.2f}%, Typ={kundentyp}"
        )

    except Exception as e:
        # Wenn Fehler → alles zurücksetzen
        conn.rollback()
        print(f"Verkauf abgebrochen. Grund: {e}")

    finally:
        # Verbindung schließen
        conn.close()


# Wenn das Skript direkt gestartet wird → main() ausführen
if __name__ == "__main__":
    main()
