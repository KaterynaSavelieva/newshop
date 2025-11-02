# purhase.py – erzeugt automatisch Einkäufe für Artikel mit geringem Lagerbestand
# Idee:
#  - Suche alle Artikel mit Lagerbestand < 3000.
#  - Finde zufällige Lieferanten, die diese Artikel liefern können.
#  - Erstelle automatisch Einkäufe (einkauf + einkaufartikel).
#
# Benötigt:
# Tabellen artikel, artikellieferant, einkauf, einkaufartikel, lieferant.

import random
from datetime import datetime
from db import get_conn

# Hilfsfunktionen
def fetch_low_stock(cur):
    """
    Sucht alle Artikel mit Lagerbestand < 3000.
    Gibt zurück: [(artikelID, name, bestand), ...]
    """
    cur.execute("""
        SELECT artikelID, produktname, lagerbestand
        FROM artikel
        WHERE lagerbestand < 4000;
    """)
    return cur.fetchall()


def pick_random_supplier(cur, artikel_id):
    """
    Wählt einen zufälligen Lieferanten für einen Artikel.
    Quelle: Tabelle artikellieferant.
    Gibt zurück: (lieferantID, einkaufspreis) oder None.
    """
    cur.execute("""
        SELECT lieferantID, einkaufspreis
        FROM artikellieferant
        WHERE artikelID = %s
        ORDER BY RAND()
        LIMIT 1;
    """, (artikel_id,))
    return cur.fetchone()


def create_header(cur, lieferant_id):
    """
    Erstellt einen neuen Einkauf (Kopfzeile in Tabelle 'einkauf').
    Rechnung wird automatisch generiert (z. B. INV-12345).
    Gibt zurück: einkaufID.
    """
    cur.execute("""
        INSERT INTO einkauf (lieferantID, einkaufsdatum, rechnung, bemerkung)
        VALUES (%s, NOW(), %s, 'Auto-Generated (smart)');
    """, (lieferant_id, f"INV-{random.randint(10000, 99999)}"))
    return cur.lastrowid


def add_item(cur, einkauf_id, artikel_id, menge, preis):
    """
    Fügt eine Position (Artikel) zum Einkauf hinzu.
    """
    cur.execute("""
        INSERT INTO einkaufartikel (einkaufID, artikelID, einkaufsmenge, einkaufspreis)
        VALUES (%s, %s, %s, %s);
    """, (einkauf_id, artikel_id, menge, preis))



# Hauptprogramm
def main():
    # Verbindung zur Datenbank herstellen
    conn = get_conn()
    if not conn:
        print("Keine Verbindung zur Datenbank.")
        return

    try:
        with conn.cursor() as cur:
            # 1️ Artikel mit niedrigem Lagerbestand holen
            low = fetch_low_stock(cur)
            if not low:
                print(" Keine Artikel mit Lagerbestand < 4000. Kein Einkauf nötig.")
                return

            # 2️ Plan für Einkäufe vorbereiten
            # Struktur: {lieferantID: [(artikelID, menge, preis), ...]}
            plan = {}
            skipped = []  # Artikel ohne Lieferant

            for artikel_id, name, bestand in low:
                sup = pick_random_supplier(cur, artikel_id)
                if not sup:
                    skipped.append((artikel_id, name))
                    continue
                lieferant_id, preis = sup

                # zufällige Menge zwischen 200 und 4000 Stück
                menge = random.randint(200, 7000)

                plan.setdefault(lieferant_id, []).append((artikel_id, menge, preis))

            if not plan:
                print("⚠Keine Lieferanten für die benötigten Artikel gefunden.")
                return

            # 3️ Einkäufe anlegen
            created = []
            for lieferant_id, items in plan.items():
                einkauf_id = create_header(cur, lieferant_id)
                for artikel_id, menge, preis in items:
                    add_item(cur, einkauf_id, artikel_id, menge, preis)
                created.append((einkauf_id, lieferant_id, len(items)))

        # 4️ Alles speichern (commit)
        conn.commit()

        # 5️ Ergebnis anzeigen
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for eid, lid, n in created:
            print(f"[{now}] ✅ Einkauf erstellt: einkaufID={eid}, Lieferant={lid}, Positionen={n}")

        if skipped:
            print("❗ Kein Lieferant für folgende Artikel:",
                  ", ".join(f"{aid}" for aid, _ in skipped))

    except Exception as e:
        # Wenn Fehler → zurückrollen
        conn.rollback()
        print(f"Fehler, Transaktion abgebrochen: {e}")

    finally:
        # Verbindung schließen
        conn.close()


# Wenn das Skript direkt gestartet wird
if __name__ == "__main__":
    main()
