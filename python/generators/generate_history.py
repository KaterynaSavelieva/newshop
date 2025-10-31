# -*- coding: utf-8 -*-
"""
generate_history.py
— Масове наповнення БД історичними даними (закупки + продажі).

Особливості:
• Стартові закупки (2024-01-01..2024-01-03) для заповнення складу.
• Генерація продажів щоденно (2024-01-04..2025-10-30), з урахуванням:
    - kundentyp.kundenrabatt (без "хардкодних" знижок);
    - правил для кількості позицій і штук за типом клієнта;
    - авто-дозакупки, якщо запас < порогу, перед продажем;
    - оновлення lagerbestand / durchschnittskosten при закупці (ковзна середня).
• Прискорення: один кеш прайсів та довідників; коміт раз на день (прогрес видно у Dashboard).
• Не потребує тригерів — все перераховується тут.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional

import pymysql
from db import get_conn

# ============================== К О Н С Т А Н Т И ==============================

# 1) Періоди
INITIAL_PURCHASES_START = date(2024, 1, 1)
INITIAL_PURCHASES_END   = date(2024, 1, 3)

SALES_START = date(2024, 1, 4)
SALES_END   = date(2025, 10, 31)

# 2) Робочі години магазину (випадковий час у межах)
STORE_OPEN_HOUR  = 9
STORE_CLOSE_HOUR = 18  # до 17:59

# 3) Початкові закупки (первинне наповнення складу)
INITIAL_PURCHASE_QTY_MIN = 200
INITIAL_PURCHASE_QTY_MAX = 1000

# 4) Автодозакупка перед продажем (коли запас не дотягує)
RESTOCK_THRESHOLD   = 20
AUTORESTOCK_QTY_MIN = 200
AUTORESTOCK_QTY_MAX = 1000

# 5) Інтенсивність чеків
RECEIPTS_PER_WEEK_MIN = 1
RECEIPTS_PER_WEEK_MAX = 7   # ⩽ 7 днів у тижні

# 6) Правила продажів за типом клієнта
TYPE_RULES: Dict[str, Dict[str, int]] = {
    "Standard": {"qty_min": 1,  "qty_max": 25,  "items_min": 1,  "items_max": 25},
    "Silber"  : {"qty_min": 1,  "qty_max": 50,  "items_min": 1,  "items_max": 50},
    "Gold"    : {"qty_min": 5,  "qty_max": 100, "items_min": 5,  "items_max": 100},
    "Platin"  : {"qty_min": 10,  "qty_max": 200, "items_min": 5,  "items_max": 200},
}

# 7) Fallback, якщо не знайшли listenpreis (дуже рідко)
VK_FALLBACK_MARKUP = 1.35

# Лог кожні N днів генерації
PROGRESS_EVERY_N_DAYS = 7


# ============================== У Т И Л І Т И ==============================

def daterange(d0: date, d1: date):
    cur = d0
    while cur <= d1:
        yield cur
        cur += timedelta(days=1)


def rand_time_in_day(d: date) -> datetime:
    h = random.randint(STORE_OPEN_HOUR, STORE_CLOSE_HOUR - 1)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return datetime(d.year, d.month, d.day, h, m, s)


def fetch_all(conn, sql: str, params: Tuple = ()) -> List[dict]:
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def fetch_one(conn, sql: str, params: Tuple = ()) -> Optional[dict]:
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def exec_one(conn, sql: str, params: Tuple = ()) -> None:
    with conn.cursor() as cur:
        cur.execute(sql, params)


def exec_many(conn, sql: str, rows: List[Tuple]) -> None:
    if not rows:
        return
    with conn.cursor() as cur:
        cur.executemany(sql, rows)


def last_id(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT LAST_INSERT_ID();")
        return int(cur.fetchone()[0])


# ============================== К Е Ш І  (довідники) ==============================

def load_articles(conn) -> List[int]:
    rows = fetch_all(conn, "SELECT artikelID FROM artikel;")
    return [int(r["artikelID"]) for r in rows]


def load_kunden_with_type(conn) -> List[dict]:
    """
    kundenID, kundentypID, type_name, rabatt (з kundentyp)
    """
    sql = """
      SELECT k.kundenID,
             k.kundentypID,
             COALESCE(kt.bezeichnung,'Standard') AS type_name,
             COALESCE(kt.kundenrabatt,0) AS rabatt
      FROM kunden k
      LEFT JOIN kundentyp kt ON kt.kundentypID = k.kundentypID
    """
    return fetch_all(conn, sql)


def load_suppliers_map(conn) -> Dict[int, List[Tuple[int, float]]]:
    """
    { artikelID: [(lieferantID, einkaufspreis), ...] }
    """
    sql = "SELECT artikelID, lieferantID, einkaufspreis FROM artikellieferant;"
    rows = fetch_all(conn, sql)
    by_art: Dict[int, List[Tuple[int, float]]] = {}
    for r in rows:
        by_art.setdefault(int(r["artikelID"]), []).append(
            (int(r["lieferantID"]), float(r["einkaufspreis"]))
        )
    return by_art


def load_latest_prices(conn) -> Dict[int, float]:
    """
    Останній дійсний listenpreis для кожного товару (MySQL 8, віконна функція).
    """
    sql = """
    SELECT artikelID, listenpreis
    FROM (
      SELECT ap.*,
             ROW_NUMBER() OVER (
               PARTITION BY ap.artikelID
               ORDER BY COALESCE(ap.gueltig_bis,'9999-12-31') DESC,
                        ap.gueltig_ab DESC
             ) AS rn
      FROM artikelpreis ap
    ) t
    WHERE t.rn = 1;
    """
    rows = fetch_all(conn, sql)
    return {int(r["artikelID"]): float(r["listenpreis"]) for r in rows}


# ==============================  С К Л А Д  ==============================

def get_stock_and_avgcost(conn, artikel_id: int) -> Tuple[int, float]:
    row = fetch_one(
        conn,
        "SELECT COALESCE(lagerbestand,0) AS qty, COALESCE(durchschnittskosten,0) AS avgc "
        "FROM artikel WHERE artikelID=%s;",
        (artikel_id,),
    )
    if not row:
        return 0, 0.0
    return int(row["qty"]), float(row["avgc"])


def inc_stock_with_avgcost(conn, artikel_id: int, qty: int, price: float) -> None:
    """
    Закупка: збільшити склад і оновити середню собівартість (ковзна).
    """
    cur_qty, cur_avg = get_stock_and_avgcost(conn, artikel_id)
    new_qty = cur_qty + qty
    total_value = (cur_qty * cur_avg) + (qty * price)
    new_avg = round(total_value / new_qty, 4) if new_qty > 0 else 0.0
    exec_one(
        conn,
        "UPDATE artikel SET lagerbestand=%s, durchschnittskosten=%s WHERE artikelID=%s;",
        (new_qty, new_avg, artikel_id),
    )


def dec_stock(conn, artikel_id: int, qty: int) -> None:
    cur_qty, _ = get_stock_and_avgcost(conn, artikel_id)
    new_qty = max(0, cur_qty - qty)
    exec_one(conn, "UPDATE artikel SET lagerbestand=%s WHERE artikelID=%s;", (new_qty, artikel_id))


# ==============================  З А К У П К И  ==============================

def create_purchase_header(conn, lieferant_id: int, when: datetime, note: str) -> int:
    exec_one(
        conn,
        "INSERT INTO einkauf (lieferantID, einkaufsdatum, rechnung, bemerkung) "
        "VALUES (%s, %s, %s, %s);",
        (lieferant_id, when, f"INV-{random.randint(10_000, 99_999)}", note),
    )
    return last_id(conn)


def add_purchase_items(conn, einkauf_id: int, items: List[Tuple[int, int, float]]) -> None:
    """
    items: [(artikelID, menge, preis), ...]
    — вставляємо рядки та оновлюємо склад.
    """
    rows = []
    for a_id, qty, price in items:
        rows.append((einkauf_id, a_id, qty, price))
        inc_stock_with_avgcost(conn, a_id, qty, price)

    exec_many(
        conn,
        "INSERT INTO einkaufartikel (einkaufID, artikelID, einkaufsmenge, einkaufspreis) "
        "VALUES (%s, %s, %s, %s);",
        rows,
    )


def initial_purchases(conn, suppliers_by_art: Dict[int, List[Tuple[int, float]]]) -> None:
    days = list(daterange(INITIAL_PURCHASES_START, INITIAL_PURCHASES_END))
    if not days:
        return

    artikel_ids = list(suppliers_by_art.keys())
    if not artikel_ids:
        return

    for d in days:
        when = rand_time_in_day(d)
        random.shuffle(artikel_ids)
        chunk = artikel_ids[: max(10, len(artikel_ids) // 3)]

        plan: Dict[int, List[Tuple[int, int, float]]] = {}
        for a_id in chunk:
            choices = suppliers_by_art.get(a_id) or []
            if not choices:
                continue
            sup_id, price = random.choice(choices)
            qty = random.randint(INITIAL_PURCHASE_QTY_MIN, INITIAL_PURCHASE_QTY_MAX)
            plan.setdefault(sup_id, []).append((a_id, qty, price))

        for sup_id, items in plan.items():
            eid = create_purchase_header(conn, sup_id, when, "Initial stock fill")
            add_purchase_items(conn, eid, items)

    conn.commit()


def restock_if_needed(conn,
                      artikel_id: int,
                      need_qty: int,
                      suppliers_by_art: Dict[int, List[Tuple[int, float]]],
                      when: datetime) -> None:
    """
    Якщо запасу не вистачає (менше need_qty) — робимо дозакупку трохи раніше цього чека.
    """
    cur_qty, _ = get_stock_and_avgcost(conn, artikel_id)
    if cur_qty >= need_qty:
        return

    choices = suppliers_by_art.get(artikel_id) or []
    if not choices:
        return

    sup_id, price = random.choice(choices)
    qty = random.randint(AUTORESTOCK_QTY_MIN, AUTORESTOCK_QTY_MAX)
    when_purchase = when - timedelta(hours=1, minutes=random.randint(5, 40))

    eid = create_purchase_header(conn, sup_id, when_purchase, "Auto restock")
    add_purchase_items(conn, eid, [(artikel_id, qty, price)])


# ==============================  П Р О Д А Ж І  ==============================

def create_sale_header(conn, kunden_id: int, when: datetime) -> int:
    exec_one(conn, "INSERT INTO verkauf (kundenID, verkaufsdatum) VALUES (%s, %s);", (kunden_id, when))
    return last_id(conn)


def add_sale_items(conn,
                   verkauf_id: int,
                   rows: List[Tuple[int, int, float, float]],
                   do_stock_update: bool = True) -> None:
    """
    rows: [(artikelID, verkaufsmenge, verkaufspreis, rabatt), ...]
    """
    exec_many(
        conn,
        "INSERT INTO verkaufartikel (verkaufID, artikelID, verkaufsmenge, verkaufspreis, rabatt) "
        "VALUES (%s, %s, %s, %s, %s);",
        [(verkauf_id, a, q, p, r) for (a, q, p, r) in rows],
    )
    if do_stock_update:
        for a, q, _, _ in rows:
            dec_stock(conn, a, q)


def weekly_receipt_days(count: int) -> List[int]:
    count = max(0, min(7, count))
    return sorted(random.sample(range(7), count))


def generate_sales(conn,
                   artikel_ids: List[int],
                   kunden: List[dict],
                   suppliers_by_art: Dict[int, List[Tuple[int, float]]],
                   price_cache: Dict[int, float]) -> None:
    if not artikel_ids or not kunden:
        return

    # розклад чеків: {(year, week, kundenID): [days]}
    schedule: Dict[Tuple[int, int, int], List[int]] = {}
    d = SALES_START
    while d <= SALES_END:
        y, w, _ = d.isocalendar()
        for k in kunden:
            k_id = int(k["kundenID"])
            cnt = random.randint(RECEIPTS_PER_WEEK_MIN, RECEIPTS_PER_WEEK_MAX)
            schedule[(y, w, k_id)] = weekly_receipt_days(cnt)
        d += timedelta(days=7)

    total_days = (SALES_END - SALES_START).days + 1
    for i, cur_day in enumerate(daterange(SALES_START, SALES_END), start=1):
        y, w, wd = cur_day.isocalendar()
        wd = wd - 1  # 0..6

        for k in kunden:
            k_id = int(k["kundenID"])
            typ_name = (k.get("type_name") or "Standard").strip()
            rabatt   = float(k.get("rabatt") or 0.0)

            if schedule.get((y, w, k_id)) and wd in schedule[(y, w, k_id)]:
                rules = TYPE_RULES.get(typ_name, TYPE_RULES["Standard"])
                items_n = random.randint(rules["items_min"], rules["items_max"])
                items_n = max(1, min(items_n, len(artikel_ids)))

                when = rand_time_in_day(cur_day)
                vk_id = create_sale_header(conn, k_id, when)

                chosen = random.sample(artikel_ids, items_n)
                rows: List[Tuple[int, int, float, float]] = []

                for a_id in chosen:
                    qty = random.randint(rules["qty_min"], rules["qty_max"])

                    # дозакупка, якщо не вистачає
                    try:
                        restock_if_needed(conn, a_id, max(RESTOCK_THRESHOLD, qty), suppliers_by_art, when)
                    except Exception:
                        pass

                    base_price = price_cache.get(a_id)
                    if base_price is None:
                        # fallback — від середньої собівартості
                        _, avgc = get_stock_and_avgcost(conn, a_id)
                        base_price = (avgc or 1.0) * VK_FALLBACK_MARKUP

                    vk_preis = round(base_price * (1.0 - rabatt / 100.0), 2)
                    rows.append((a_id, qty, vk_preis, rabatt))

                add_sale_items(conn, vk_id, rows)

        conn.commit()
        if i % PROGRESS_EVERY_N_DAYS == 0 or i == total_days:
            print(f"  • committed day {i}/{total_days}: {cur_day.isoformat()}")


# ==============================  М Е Й Н  ==============================

def clear_all(conn) -> None:
    """Очистити попередні дані генерації й обнулити склад."""
    exec_one(conn, "DELETE FROM verkaufartikel;")
    exec_one(conn, "DELETE FROM verkauf;")
    exec_one(conn, "DELETE FROM einkaufartikel;")
    exec_one(conn, "DELETE FROM einkauf;")
    exec_one(conn, "UPDATE artikel SET lagerbestand=0, durchschnittskosten=NULL;")
    conn.commit()


def main() -> None:
    conn = get_conn()
    if not conn:
        print("Keine Verbindung zur Datenbank")
        return

    try:
        random.seed(42)

        print("• Cleaning data …")
        clear_all(conn)
        print("  done.")

        print("• Loading dictionaries …")
        artikel_ids      = load_articles(conn)
        kunden           = load_kunden_with_type(conn)
        suppliers_by_art = load_suppliers_map(conn)
        price_cache      = load_latest_prices(conn)
        print(f"  artikel={len(artikel_ids)}, kunden={len(kunden)}, suppliers={len(suppliers_by_art)}, priced={len(price_cache)}")

        print("• Initial purchases …")
        initial_purchases(conn, suppliers_by_art)
        print("  done.")

        print("• Generating sales …")
        generate_sales(conn, artikel_ids, kunden, suppliers_by_art, price_cache)
        print("  done.")

    except KeyboardInterrupt:
        conn.rollback()
        print("\n⛔️ Stopped by user (Ctrl+C). Rolled back current transaction.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Fehler, Transaktion abgebrochen: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
