# sale.py
"""
Генерація ОДНОГО продажу з діапазонами, що залежать від типу клієнта:
Standard →   menge 1–25,   max_items 1–50
Silber   →   menge 1–50,   max_items 1–25
Gold     →   menge 1–100,  max_items 1–100
Platin   →   menge 1–150,  max_items 1–150
"""

import random
from datetime import datetime
from db import get_conn


# ──────────────────────────────────────────────────────────────────────────────
# Допоміжні
# ──────────────────────────────────────────────────────────────────────────────

def ranges_for_type(kundentyp: str):
    """Повертає ((min_menge, max_menge), (min_items, max_items)) для заданого типу."""
    t = (kundentyp or "Standard").strip().lower()
    if t == "standard":
        return (1, 25), (1, 25)
    if t == "silber":
        return (1, 50), (1, 50)
    if t == "gold":
        return (1, 100), (1, 100)
    if t == "platin":
        return (1, 150), (1, 150)
    # дефолт — як Standard
    return (1, 25), (1, 25)


def pick_customer(cur):
    """
    Вибираємо випадкового клієнта, його знижку та тип.
    Повертає: (kundenID, rabatt_pct, kundentyp_name)
    """
    cur.execute("""
        SELECT k.kundenID,
               COALESCE(t.kundenrabatt, 0)  AS rabatt,
               COALESCE(t.bezeichnung, 'Standard') AS typ
        FROM kunden k
        LEFT JOIN kundentyp t ON t.kundentypID = k.kundentypID
        ORDER BY RAND()
        LIMIT 1;
    """)
    row = cur.fetchone()
    if not row:
        raise RuntimeError("У таблиці 'kunden' немає даних.")
    return row[0], float(row[1]), str(row[2])


def create_sale_header(cur, kunden_id, when=None):
    when = when or datetime.now()
    cur.execute("INSERT INTO verkauf(kundenID, verkaufsdatum) VALUES(%s, %s);", (kunden_id, when))
    return cur.lastrowid, when


def pick_articles_with_stock(cur, max_items=5):
    """Беремо випадкові товари з наявним залишком."""
    cur.execute("""
        SELECT artikelID, lagerbestand
        FROM artikel
        WHERE lagerbestand > 0
        ORDER BY RAND()
        LIMIT %s;
    """, (max_items,))
    return cur.fetchall()  # [(artikelID, lagerbestand), ...]


def get_listenpreis(cur, artikel_id, when):
    """Актуальна ціна з artikelpreis на момент 'when'."""
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


def add_sale_items(cur, verkauf_id, items, when, rabatt_pct, menge_range):
    """
    Додає позиції у продаж.
    items: список (artikelID, lagerbestand)
    menge_range: (min_menge, max_menge) — залежить від типу клієнта
    Повертає (added_count, sum_without_rabatt).
    """
    added = 0
    total = 0.0
    min_m, max_m = menge_range

    for artikel_id, stock in items:
        if stock <= 0:
            continue

        # кількість в межах типового діапазону, але не більше складу
        menge = random.randint(min_m, max_m)
        menge = min(menge, stock)
        if menge <= 0:
            continue

        preis = get_listenpreis(cur, artikel_id, when)

        cur.execute("""
            INSERT INTO verkaufartikel(verkaufID, artikelID, verkaufsmenge, verkaufspreis, rabatt)
            VALUES (%s, %s, %s, %s, %s);
        """, (verkauf_id, artikel_id, menge, preis, rabatt_pct))

        added += 1
        total += preis * menge

    return added, round(total, 2)


# ──────────────────────────────────────────────────────────────────────────────
# Основний сценарій
# ──────────────────────────────────────────────────────────────────────────────

def main():
    conn = get_conn()
    if not conn:
        print("Keine Verbindung zur Datenbank")
        return

    try:
        with conn.cursor() as cur:
            # 1) клієнт: ID, знижка, тип
            kunden_id, rabatt_pct, kundentyp = pick_customer(cur)

            # 2) діапазони залежно від типу
            menge_range, items_range = ranges_for_type(kundentyp)

            # 3) шапка продажу
            verkauf_id, when = create_sale_header(cur, kunden_id)

            # 4) скільки товарів у чеку — залежить від типу
            max_items = random.randint(*items_range)
            candidates = pick_articles_with_stock(cur, max_items=max_items)

            if not candidates:
                raise RuntimeError("Keine Produkte auf Lager (>0). Verkauf abgebrochen")

            # 5) додаємо позиції з діапазоном кількості за типом
            added, total = add_sale_items(cur, verkauf_id, candidates, when, rabatt_pct, menge_range)

            if added == 0:
                raise RuntimeError("Keine Artikel hinzugefügt (möglicherweise Lagerbestand=0). Verkauf abgebrochen.")

        conn.commit()
        print(
            f"Verkauf erstellt: verkaufID={verkauf_id}, позицій={added}, "
            f"сума(без знижок)={total}, Kundenrabatt={rabatt_pct}%, Typ={kundentyp}"
        )
    except Exception as e:
        conn.rollback()
        print(f"Verkauf abgebrochen. Grund: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
