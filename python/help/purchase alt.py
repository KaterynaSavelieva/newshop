# 🔹 Генерація випадкових закупок у період 01.01.2025–30.06.2025
# 🔹 Якщо запас товару < 100 → створюємо закупку у випадкового постачальника
# 🔹 Кількість на позицію: випадково 25–120
# 🔹 Якщо в одного постачальника кілька таких товарів — робимо ОДИН документ на постачальника
# 🔹 Дата закупки: випадкова між 2025-01-01 і 2025-06-30

import random
from datetime import datetime, timedelta
from db import get_conn


def random_date(start, end):
    """Повертає випадкову дату між start і end"""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def fetch_low_stock(cur):
    # товари з запасом < 100
    cur.execute("""
        SELECT artikelID, produktname, lagerbestand
        FROM artikel
        WHERE lagerbestand < 100;
    """)
    return cur.fetchall()


def pick_random_supplier(cur, artikel_id):
    # випадковий постачальник для товару
    cur.execute("""
        SELECT lieferantID, einkaufspreis
        FROM artikellieferant
        WHERE artikelID = %s
        ORDER BY RAND()
        LIMIT 1;
    """, (artikel_id,))
    return cur.fetchone()  # (lieferantID, preis) або None


def create_header(cur, lieferant_id, einkaufsdatum):
    # створюємо заголовок закупки з випадковою датою
    cur.execute("""
        INSERT INTO einkauf (lieferantID, einkaufsdatum, rechnung, bemerkung)
        VALUES (%s, %s, %s, 'Auto-Generated (random period)')
    """, (lieferant_id, einkaufsdatum, f"INV-{random.randint(10000, 99999)}"))
    return cur.lastrowid


def add_item(cur, einkauf_id, artikel_id, menge, preis):
    # додаємо позицію закупки
    cur.execute("""
        INSERT INTO einkaufartikel (einkaufID, artikelID, einkaufsmenge, einkaufspreis)
        VALUES (%s, %s, %s, %s)
    """, (einkauf_id, artikel_id, menge, preis))


def main():
    start_date = datetime(2025, 2, 15)
    end_date = datetime(2025, 3, 3)

    conn = get_conn()
    if not conn:
        print("❌ Keine Verbindung zur Datenbank")
        return

    try:
        with conn.cursor() as cur:
            low = fetch_low_stock(cur)
            if not low:
                print("ℹ️ Keine Produkte mit Lagerbestand < 100. Kein Einkauf erforderlich.")
                return

            plan = {}
            skipped = []

            # формуємо план закупок
            for artikel_id, name, bestand in low:
                sup = pick_random_supplier(cur, artikel_id)
                if not sup:
                    skipped.append((artikel_id, name))
                    continue
                lieferant_id, preis = sup
                menge = random.randint(25, 120)
                plan.setdefault(lieferant_id, []).append((artikel_id, menge, preis))

            if not plan:
                print("⚠️ Keine verfügbaren Lieferanten gefunden.")
                return

            created = []
            for lieferant_id, items in plan.items():
                einkaufsdatum = random_date(start_date, end_date)
                einkauf_id = create_header(cur, lieferant_id, einkaufsdatum)
                for artikel_id, menge, preis in items:
                    add_item(cur, einkauf_id, artikel_id, menge, preis)
                created.append((einkauf_id, lieferant_id, einkaufsdatum, len(items)))

        conn.commit()

        # Звіт у консоль
        print("✅ Zufällige Einkäufe wurden erfolgreich erstellt:")
        for eid, lid, datum, n in created:
            print(f"   → EinkaufID={eid}, Lieferant={lid}, Datum={datum.date()}, Positionen={n}")

        if skipped:
            print("⚠️ Artikel ohne Lieferanten:", ", ".join(f"{aid}" for aid, _ in skipped))

    except Exception as e:
        conn.rollback()
        print(f"❌ Fehler, Transaktion abgebrochen: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
