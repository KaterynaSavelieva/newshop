# sale_period.py
"""
Генерація ВИПАДКОВИХ продажів у періоді:
  01.01.2025 – 30.06.2025

Правила:
- ціна одиниці = актуальний artikelpreis.listenpreis на момент продажу
- у чеку 1–5 позицій; для кожної позиції кількість 1–25 (але не більше наявного складу)
- беруться тільки товари з lagerbestand > 0
- застосовується знижка клієнта (kundenrabatt) — пишемо у поле 'rabatt' як %
- тригери самі списують склад та валідуть кількість
"""

import random
from datetime import datetime, timedelta
from db import get_conn

# ── Налаштування (за потреби зміни) ────────────────────────────────────────────
START_DATE = datetime(2025, 9, 1)
END_DATE   = datetime(2025, 9, 30)
SALES_PER_DAY_MIN = 1     # мінімум чеків на день
SALES_PER_DAY_MAX = 20     # максимум чеків на день
HOUR_FROM = 8             # продажі з 08:00
HOUR_TO   = 20            # … до 20:59
# ──────────────────────────────────────────────────────────────────────────────


def rand_time_on_day(day: datetime) -> datetime:
    """Випадковий час усередині робочого дня [HOUR_FROM..HOUR_TO]."""
    hour = random.randint(HOUR_FROM, HOUR_TO)
    minute = random.randint(0, 59)
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def pick_customer(cur):
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


def create_sale_header(cur, kunden_id, when: datetime):
    cur.execute(
        "INSERT INTO verkauf(kundenID, verkaufsdatum) VALUES(%s, %s);",
        (kunden_id, when)
    )
    return cur.lastrowid


def pick_articles_with_stock(cur, max_items=5):
    cur.execute("""
        SELECT artikelID, lagerbestand
        FROM artikel
        WHERE lagerbestand > 0
        ORDER BY RAND()
        LIMIT %s;
    """, (max_items,))
    return cur.fetchall()  # [(artikelID, lagerbestand), ...]


def get_listenpreis(cur, artikel_id, when: datetime) -> float:
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
        raise RuntimeError(
            f"Немає прайсу в 'artikelpreis' для artikelID={artikel_id} на {when.date()}."
        )
    return float(row[0])


def add_sale_items(cur, verkauf_id, items, when, rabatt_pct):
    added = 0
    total = 0.0
    for artikel_id, stock in items:
        if stock <= 0:
            continue
        menge = random.randint(1, 25)
        menge = min(menge, stock)

        preis = get_listenpreis(cur, artikel_id, when)

        cur.execute("""
            INSERT INTO verkaufartikel(verkaufID, artikelID, verkaufsmenge, verkaufspreis, rabatt)
            VALUES (%s, %s, %s, %s, %s);
        """, (verkauf_id, artikel_id, menge, preis, rabatt_pct))

        added += 1
        total += preis * menge
    return added, round(total, 2)


def generate_one_sale(cur, when: datetime):
    kunden_id, rabatt_pct = pick_customer(cur)

    verkauf_id = create_sale_header(cur, kunden_id, when)

    max_items = random.randint(1, 5)
    candidates = pick_articles_with_stock(cur, max_items=max_items)
    if not candidates:
        raise RuntimeError("Немає товарів з наявним складом (>0).")

    added, total = add_sale_items(cur, verkauf_id, candidates, when, rabatt_pct)
    if added == 0:
        raise RuntimeError("Жодну позицію не додано (можливо, склад=0).")

    return verkauf_id, added, total, rabatt_pct


def main():
    conn = get_conn()
    if not conn:
        print("❌ Немає підключення до БД.")
        return

    total_sales = 0
    total_items = 0
    total_sum   = 0.0
    skipped_days = 0

    try:
        with conn.cursor() as cur:
            day = START_DATE
            while day <= END_DATE:
                sales_today = random.randint(SALES_PER_DAY_MIN, SALES_PER_DAY_MAX)
                made_today = 0

                for _ in range(sales_today):
                    when = rand_time_on_day(day)
                    try:
                        vid, cnt, summ, rabatt = generate_one_sale(cur, when)
                        total_sales += 1
                        total_items += cnt
                        total_sum   += summ
                        made_today += 1
                        # (без зайвого спаму у консоль; за бажанням можна розкоментувати)
                        # print(f"✓ {when.date()} sale #{vid} items={cnt} sum={summ} rabatt={rabatt}%")
                    except Exception as e:
                        # Якщо на якомусь кроці не вдалося (нема прайсу тощо) — просто пропускаємо цю спробу
                        # і йдемо далі, щоб не зривати весь масив.
                        # print(f"… пропущено: {e}")
                        pass

                if made_today == 0:
                    skipped_days += 1

                day += timedelta(days=1)

        conn.commit()
        print("✅ Готово!")
        print(f"   Продажів створено: {total_sales}")
        print(f"   Позицій у чеках:   {total_items}")
        print(f"   Сума (без знижок): {round(total_sum, 2)} €")
        if skipped_days:
            print(f"   Днів без продажів (через брак даних/цін): {skipped_days}")

    except Exception as e:
        conn.rollback()
        print(f"⚠️ Помилка, транзакцію відмінено: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
