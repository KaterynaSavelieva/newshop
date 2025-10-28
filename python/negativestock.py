# fix_negative_stock.py  — RANDOM supplier version
import math
from datetime import datetime, timedelta
from db import get_conn

TAG_NOTE = "Auto-fix negative stock"

def fetch_negatives(cur):
    cur.execute("""
        SELECT datum, artikelID, produktname, bestand_tag
        FROM v_bestand_verlauf
        WHERE bestand_tag < 0
        ORDER BY datum, artikelID
    """)
    return cur.fetchall()

def pick_supplier(cur, artikel_id):
    """Випадковий постачальник з artikellieferant для цього товару."""
    cur.execute("""
        SELECT lieferantID, einkaufspreis
        FROM artikellieferant
        WHERE artikelID = %s
        ORDER BY RAND()
        LIMIT 1
    """, (artikel_id,))
    return cur.fetchone()

def find_existing_header(cur, lieferant_id, einkaufs_datum):
    """Шукаємо вже створену шапку на цього постачальника і дату з нашим тегом."""
    cur.execute("""
        SELECT einkaufID
        FROM einkauf
        WHERE lieferantID = %s
          AND DATE(einkaufsdatum) = %s
          AND bemerkung = %s
        LIMIT 1
    """, (lieferant_id, einkaufs_datum.date(), TAG_NOTE))
    row = cur.fetchone()
    return row[0] if row else None

def create_header(cur, lieferant_id, einkaufs_dt):
    cur.execute("""
        INSERT INTO einkauf(lieferantID, einkaufsdatum, rechnung, bemerkung)
        VALUES (%s, %s, %s, %s)
    """, (lieferant_id, einkaufs_dt, f"AUTO-{einkaufs_dt:%Y%m%d}-{lieferant_id}", TAG_NOTE))
    return cur.lastrowid

def add_item(cur, einkauf_id, artikel_id, menge, preis):
    cur.execute("""
        INSERT INTO einkaufartikel (einkaufID, artikelID, einkaufsmenge, einkaufspreis)
        VALUES (%s, %s, %s, %s)
    """, (einkauf_id, artikel_id, menge, preis))

def main():
    conn = get_conn()
    if not conn:
        print("❌ Keine DB-Verbindung")
        return

    created_headers = 0
    created_items = 0
    skipped_no_supplier = set()

    try:
        with conn.cursor() as cur:
            rows = fetch_negatives(cur)
            headers_cache = {}  # ключ: (lieferantID, date) → einkaufID

            for datum, artikel_id, name, bestand_tag in rows:
                # дата закупки = попередній день о 10:00
                if isinstance(datum, str):
                    day = datetime.fromisoformat(datum).date()
                else:
                    day = datum
                purch_dt = datetime.combine(day - timedelta(days=1), datetime.min.time()).replace(hour=10)

                sup = pick_supplier(cur, artikel_id)
                if not sup:
                    skipped_no_supplier.add(artikel_id)
                    continue
                lieferant_id, preis = sup

                # кількість = |мінус| * 1.10 і вгору
                deficit = abs(float(bestand_tag))
                menge = max(1, int(math.ceil(deficit * 1.10)))

                # беремо/створюємо шапку для (постачальник, дата)
                key = (lieferant_id, purch_dt.date())
                einkauf_id = headers_cache.get(key)
                if not einkauf_id:
                    einkauf_id = find_existing_header(cur, lieferant_id, purch_dt)
                    if not einkauf_id:
                        einkauf_id = create_header(cur, lieferant_id, purch_dt)
                        created_headers += 1
                    headers_cache[key] = einkauf_id

                add_item(cur, einkauf_id, artikel_id, menge, float(preis))
                created_items += 1

        conn.commit()
        print(f"✅ Авто-закупок (шапок) створено: {created_headers}")
        print(f"✅ Додано позицій: {created_items}")
        if skipped_no_supplier:
            print("⚠️ Немає постачальників у artikellieferant для артикулів:",
                  ", ".join(map(str, sorted(skipped_no_supplier))))
    except Exception as e:
        conn.rollback()
        print(f"⚠️ Відкат транзакції: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
