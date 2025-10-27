# sale.py
"""
Генерація ОДНОГО продажу за правилами:
- ціна одиниці = artikelpreis.listenpreis, актуальна на дату продажу
- 1–5 позицій у чеку; для кожної позиції кількість 1–5 (але не більше наявного складу)
- беруться тільки товари з lagerbestand > 0
- застосовується знижка клієнта (kundenrabatt) — пишемо у поле 'rabatt' як %
- тригери самі списують склад та валідуть кількість
"""

import random
from datetime import datetime
from db import get_conn


def pick_customer(cur):
    # вибираємо випадкового клієнта і його знижку
    cur.execute("""
        SELECT k.kundenID, COALESCE(t.kundenrabatt,0)
        FROM kunden k
        LEFT JOIN kundentyp t ON t.kundentypID = k.kundentypID
        ORDER BY RAND() LIMIT 1;
    """)
    row = cur.fetchone()
    if not row:
        raise RuntimeError("У таблиці 'kunden' немає даних.")
    return row[0], float(row[1])


def create_sale_header(cur, kunden_id, when=None):
    when = when or datetime.now()
    cur.execute("INSERT INTO verkauf(kundenID, verkaufsdatum) VALUES(%s, %s);", (kunden_id, when))
    return cur.lastrowid, when


def pick_articles_with_stock(cur, max_items=5):
    # беремо довільні товари з наявним залишком
    cur.execute("""
        SELECT artikelID, lagerbestand
        FROM artikel
        WHERE lagerbestand > 0
        ORDER BY RAND()
        LIMIT %s;
    """, (max_items,))
    return cur.fetchall()  # [(artikelID, lagerbestand), ...]


def get_listenpreis(cur, artikel_id, when):
    # актуальна ціна з artikelpreis на момент 'when'
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
        raise RuntimeError(f"Немає прайс-рядка в 'artikelpreis' для artikelID={artikel_id} на дату {when}.")
    return float(row[0])


def add_sale_items(cur, verkauf_id, items, when, rabatt_pct):
    """
    items: список (artikelID, lagerbestand)
    Повертає кількість доданих позицій та суму по чеку (без урах. знижки, бо в таблиці зберігаємо ціну одиниці до знижки).
    """
    added = 0
    total = 0.0
    for artikel_id, stock in items:
        # кількість 1–25, але не більше stock
        if stock <= 0:
            continue
        menge = random.randint(1, 25)
        menge = min(menge, stock)

        # ціна одиниці = listenpreis
        preis = get_listenpreis(cur, artikel_id, when)

        # вставляємо рядок продажу; тригер перевірить залишок і спише склад
        cur.execute("""
            INSERT INTO verkaufartikel(verkaufID, artikelID, verkaufsmenge, verkaufspreis, rabatt)
            VALUES (%s, %s, %s, %s, %s);
        """, (verkauf_id, artikel_id, menge, preis, rabatt_pct))

        added += 1
        total += preis * menge  # сума без урахування знижки
    return added, round(total, 2)


def main():
    conn = get_conn()
    if not conn:
        print("❌ Немає підключення до БД.")
        return

    try:
        with conn.cursor() as cur:
            # 1) клієнт і його знижка
            kunden_id, rabatt_pct = pick_customer(cur)

            # 2) випадкова дата у вересні 2025 (випадковий день і час)
            day = random.randint(1, 30)
            hour = random.randint(8, 20)
            minute = random.randint(0, 59)
            when = datetime(2025, 7, day, hour, minute, 0)

            # 3) шапка продажу
            verkauf_id, when = create_sale_header(cur, kunden_id, when)

            # 4) добираємо 1–5 товарів із наявним складом
            max_items = random.randint(1, 25)
            candidates = pick_articles_with_stock(cur, max_items=max_items)

            if not candidates:
                raise RuntimeError("Немає товарів з наявним складом (>0). Продаж скасовано.")

            # 5) додаємо позиції
            added, total = add_sale_items(cur, verkauf_id, candidates, when, rabatt_pct)

            if added == 0:
                # якщо нічого не додали — скасовуємо шапку
                raise RuntimeError("Жодну позицію не додано (можливо, склад=0). Продаж скасовано.")

        conn.commit()
        print(f"✅ Продаж створено: verkaufID={verkauf_id}, позицій={added}, сума(без знижок)={total}, "
              f"дата={when.date()}, знижка клієнта={rabatt_pct}%")
    except Exception as e:
        conn.rollback()
        print(f"⚠️ Продаж скасовано. Причина: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
