# purchase.py
"""
Створює ОДНУ закупку:
- постачальник: випадковий
- позицій у закупці: 1–8
- товари: тільки ті, що прив'язані до постачальника (artikellieferant)
- кількість на позицію: 10–100
- ціна закупки: artikellieferant.einkaufspreis (без коливань)
- дата закупки: NOW()
Тригери на 'einkaufartikel' автоматично оновлять склад і середню собівартість.
"""

import random
from datetime import datetime
from db import get_conn

def pick_supplier(cur):
    cur.execute("SELECT lieferantID FROM lieferanten ORDER BY RAND() LIMIT 1;")
    row = cur.fetchone()
    if not row:
        raise RuntimeError("У таблиці 'lieferanten' немає даних.")
    return row[0]

def create_purchase_header(cur, lieferant_id, when=None):
    when = when or datetime.now()
    cur.execute(
        "INSERT INTO einkauf(lieferantID, einkaufsdatum, rechnung, bemerkung) VALUES(%s,%s,%s,%s);",
        (lieferant_id, when, f"INV-{random.randint(10000,99999)}", "Auto-Generated")
    )
    return cur.lastrowid, when

def supplier_articles(cur, lieferant_id, limit_n):
    # товари, які постачає цей постачальник, разом з їх ціною закупки
    cur.execute("""
        SELECT al.artikelID, al.einkaufspreis
        FROM artikellieferant al
        WHERE al.lieferantID = %s
        ORDER BY RAND()
        LIMIT %s;
    """, (lieferant_id, limit_n))
    return cur.fetchall()  # [(artikelID, einkaufspreis), ...]

def add_purchase_items(cur, einkauf_id, rows):
    total_positions = 0
    for artikel_id, ek_preis in rows:
        menge = random.randint(10, 100)  # 10–100
        cur.execute("""
            INSERT INTO einkaufartikel(einkaufID, artikelID, einkaufsmenge, einkaufspreis)
            VALUES (%s,%s,%s,%s);
        """, (einkauf_id, artikel_id, menge, ek_preis))
        total_positions += 1
    return total_positions

def main():
    conn = get_conn()
    if not conn:
        print("❌ Немає підключення до БД.")
        return
    try:
        with conn.cursor() as cur:
            # 1) випадковий постачальник
            lieferant_id = pick_supplier(cur)

            # 2) заголовок закупки
            einkauf_id, when = create_purchase_header(cur, lieferant_id)

            # 3) оберемо 1–8 позицій із номенклатури постачальника
            limit_n = random.randint(1, 8)
            items = supplier_articles(cur, lieferant_id, limit_n)
            if not items:
                raise RuntimeError(f"У постачальника {lieferant_id} немає прив'язаних товарів у 'artikellieferant'.")

            # 4) додамо позиції (тригери оновлять склад/собівартість)
            added = add_purchase_items(cur, einkauf_id, items)

        conn.commit()
        print(f"✅ Закупка створена: einkaufID={einkauf_id}, постачальник={lieferant_id}, позицій={added}, дата={when}")
    except Exception as e:
        conn.rollback()
        print(f"⚠️ Закупку скасовано. Причина: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
