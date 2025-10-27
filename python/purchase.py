# 🔹 Якщо запас товару < 20 → робимо закупку у випадкового постачальника,
#    який має прив'язку в artikellieferant.
# 🔹 К-сть на позицію: випадково 30..80
# 🔹 Якщо в одного постачальника кілька таких товарів — робимо ОДИН документ на постачальника.
# 🔹 Дата закупки: NOW()

import random
from datetime import datetime
from db import get_conn

def fetch_low_stock(cur):
    # товари з запасом < 20
    cur.execute("SELECT artikelID, produktname, lagerbestand FROM artikel WHERE lagerbestand < 25;")
    return cur.fetchall()  # [(artikelID, name, bestand), ...]

def pick_random_supplier(cur, artikel_id):
    # будь-який постачальник, що має цей товар у artikellieferant
    cur.execute("""
        SELECT lieferantID, einkaufspreis
        FROM artikellieferant
        WHERE artikelID = %s
        ORDER BY RAND()
        LIMIT 1;
    """, (artikel_id,))
    return cur.fetchone()  # (lieferantID, preis) або None

def create_header(cur, lieferant_id):
    # створюємо заголовок закупки
    cur.execute("""
        INSERT INTO einkauf (lieferantID, einkaufsdatum, rechnung, bemerkung)
        VALUES (%s, NOW(), %s, 'Auto-Generated (smart)')
    """, (lieferant_id, f"INV-{random.randint(10000, 99999)}"))
    return cur.lastrowid

def add_item(cur, einkauf_id, artikel_id, menge, preis):
    # додаємо позицію закупки
    cur.execute("""
        INSERT INTO einkaufartikel (einkaufID, artikelID, einkaufsmenge, einkaufspreis)
        VALUES (%s, %s, %s, %s)
    """, (einkauf_id, artikel_id, menge, preis))

def main():
    conn = get_conn()
    if not conn:
        print("❌ Немає підключення до БД.")
        return

    try:
        with conn.cursor() as cur:
            low = fetch_low_stock(cur)
            if not low:
                print("ℹ️ Немає товарів з запасом < 20. Закупка не потрібна.")
                return

            # згрупуємо товари за постачальником: {lieferantID: [(artikelID, menge, preis), ...]}
            plan = {}
            skipped = []

            for artikel_id, name, bestand in low:
                sup = pick_random_supplier(cur, artikel_id)
                if not sup:
                    skipped.append((artikel_id, name))
                    continue
                lieferant_id, preis = sup
                menge = random.randint(30, 80)  # 1B: випадково 30..80
                plan.setdefault(lieferant_id, []).append((artikel_id, menge, preis))

            if not plan:
                print("⚠️ Немає жодного доступного постачальника для потрібних товарів.")
                return

            created = []
            for lieferant_id, items in plan.items():
                einkauf_id = create_header(cur, lieferant_id)
                for artikel_id, menge, preis in items:
                    add_item(cur, einkauf_id, artikel_id, menge, preis)
                created.append((einkauf_id, lieferant_id, len(items)))

        conn.commit()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for eid, lid, n in created:
            print(f"✅ [{now}] Закупка створена: einkaufID={eid}, постачальник={lid}, позицій={n}")
        if skipped:
            print("⚠️ Пропущені (нема прив'язки в artikellieferant):",
                  ", ".join(f"{aid}" for aid, _ in skipped))
    except Exception as e:
        conn.rollback()
        print(f"❌ Помилка, транзакцію скасовано: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()