# python/generators/auto_restock.py
import random
from datetime import date, datetime, timedelta
from db import get_conn

DATE_FROM = date(2025, 1, 1)
DATE_TO   = date.today()
THRESHOLD = 300
QTY_MIN   = 200
QTY_MAX   = 1000
PRICE_MIN_COEF = 0.60
PRICE_MAX_COEF = 0.90

SQL_LOW_STOCK = """
    SELECT tag, artikelID, bestand
    FROM v_bestand_wert_tag
    WHERE tag BETWEEN %s AND %s
      AND bestand < %s
    ORDER BY tag, artikelID
"""

SQL_GET_SUPPLIER = """
    SELECT COALESCE(lieferantID, 1) AS lieferantID
    FROM artikel
    WHERE artikelID = %s
"""

SQL_PRICE_AT_DATE = """
    SELECT listenpreis
    FROM artikelpreis
    WHERE artikelID = %s
      AND gueltig_ab <= %s
      AND (gueltig_bis IS NULL OR gueltig_bis >= %s)
    ORDER BY gueltig_ab DESC
    LIMIT 1
"""

SQL_EXISTS_LINE = """
    SELECT ea.einkaufID
    FROM einkauf e
    JOIN einkaufartikel ea ON ea.einkaufID = e.einkaufID
    WHERE ea.artikelID = %s
      AND e.einkaufdatum >= %s
      AND e.einkaufdatum <  %s
    LIMIT 1
"""

def has_column(cur, table: str, column: str) -> bool:
    cur.execute("""
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = %s
          AND COLUMN_NAME  = %s
        LIMIT 1
    """, (table, column))
    return cur.fetchone() is not None

def pick_purchase_price(cur, artikel_id: int, when_dt: datetime) -> float:
    cur.execute(SQL_PRICE_AT_DATE, (artikel_id, when_dt, when_dt))
    row = cur.fetchone()
    base = float(row[0]) if row else 1.0
    coef = random.uniform(PRICE_MIN_COEF, PRICE_MAX_COEF)
    return round(base * coef, 2)

def ensure_no_duplicate(cur, artikel_id: int, einkauf_date: date) -> bool:
    start_dt = datetime.combine(einkauf_date, datetime.min.time())
    end_dt   = start_dt + timedelta(days=1)
    cur.execute(SQL_EXISTS_LINE, (artikel_id, start_dt, end_dt))
    return cur.fetchone() is not None

def run():
    conn = get_conn()
    if not conn:
        print("Keine DB-Verbindung")
        return

    created_rows = 0
    created_docs = 0

    try:
        with conn.cursor() as cur:
            # Чи є поля bemerkung?
            has_bem_e  = has_column(cur, "einkauf", "bemerkung")
            has_bem_ea = has_column(cur, "einkaufartikel", "bemerkung")

            cur.execute(SQL_LOW_STOCK, (DATE_FROM, DATE_TO, THRESHOLD))
            low_rows = cur.fetchall()

            for tag, artikel_id, bestand in low_rows:
                buy_on = tag - timedelta(days=1)
                buy_dt = datetime.combine(buy_on, datetime.min.time()) + timedelta(hours=9)

                if ensure_no_duplicate(cur, artikel_id, buy_on):
                    continue

                cur.execute(SQL_GET_SUPPLIER, (artikel_id,))
                sup_row = cur.fetchone()
                lieferant_id = int(sup_row[0]) if sup_row else 1

                menge = random.randint(QTY_MIN, QTY_MAX)
                preis = pick_purchase_price(cur, artikel_id, buy_dt)

                # Будуємо текст примітки
                header_note = (
                    f"AutoRestock: Bestand {bestand} < {THRESHOLD} am {tag.isoformat()}, "
                    f"Kauf am {buy_on.isoformat()}"
                )
                line_note = (
                    f"AutoRestock: +{menge} Stk; Preis={preis:.2f}; "
                    f"Schwelle<{THRESHOLD}; Bestand={bestand} am {tag.isoformat()}"
                )

                # Вставка шапки
                if has_bem_e:
                    cur.execute(
                        "INSERT INTO einkauf(lieferantID, einkaufdatum, bemerkung) VALUES (%s, %s, %s)",
                        (lieferant_id, buy_dt, header_note),
                    )
                else:
                    cur.execute(
                        "INSERT INTO einkauf(lieferantID, einkaufdatum) VALUES (%s, %s)",
                        (lieferant_id, buy_dt),
                    )
                einkauf_id = cur.lastrowid
                created_docs += 1

                # Вставка рядка
                if has_bem_ea:
                    cur.execute(
                        "INSERT INTO einkaufartikel(einkaufID, artikelID, einkaufsmenge, einkaufspreis, bemerkung) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (einkauf_id, artikel_id, menge, preis, line_note),
                    )
                else:
                    cur.execute(
                        "INSERT INTO einkaufartikel(einkaufID, artikelID, einkaufsmenge, einkaufspreis) "
                        "VALUES (%s, %s, %s, %s)",
                        (einkauf_id, artikel_id, menge, preis),
                    )

                created_rows += 1

        conn.commit()
        print(f"Auto-Restock: erstellt {created_docs} Einkaufsbeleg(e), {created_rows} Position(en).")
    except Exception as e:
        # ✔ rollback Є
        conn.rollback()
        print("Auto-Restock abgebrochen:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    run()
