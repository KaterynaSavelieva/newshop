# -*- coding: utf-8 -*-
"""
generate_history.py
Erzeugt viele Testdaten für die Datenbank: Einkäufe (einkauf/einkaufartikel) + Verkäufe (verkauf/verkaufartikel).

Was das Skript macht (kurz und einfach):
• Am Anfang (01.–03.01.2024) werden große Anfangs-Einkäufe gemacht → Lager wird gefüllt.
• Danach (04.01.2024–31.10.2025) werden jeden Tag Verkäufe erzeugt.
• Kundentypen (Standard/Silber/Gold/Platin) steuern: wie viele Artikel pro Bon und wie viele Stück.
• Rabatt kommt aus kundentyp.kundenrabatt (keine festen „Hardcode“-Rabatte).
• Wenn Lager für einen Artikel zu klein ist → vor dem Verkauf automatisch nachkaufen.
• Beim Einkauf wird lagerbestand erhöht und durchschnittskosten (Durchschnittspreis) neu berechnet.
• Es wird schneller, weil wir einmal am Tag „committen“ und viele Nachschlage-Daten cachen.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple, Optional

import pymysql
from db import get_conn  # eigene Funktion: verbindet zur DB (liest .env)

# ============================== K O N S T A N T E N ==============================

# 1) Zeiträume
INITIAL_PURCHASES_START = date(2024, 1, 1)   # Start für Anfangs-Einkäufe
INITIAL_PURCHASES_END   = date(2024, 1, 3)   # Ende für Anfangs-Einkäufe

SALES_START = date(2024, 1, 4)               # Start für tägliche Verkäufe
SALES_END   = date(2025, 10, 31)             # Ende für tägliche Verkäufe

# 2) Öffnungszeiten (für zufällige Uhrzeit eines Verkaufs)
STORE_OPEN_HOUR  = 9
STORE_CLOSE_HOUR = 18  # bis 17:59

# 3) Anfangseinkäufe: wie viele Stück pro Artikel
INITIAL_PURCHASE_QTY_MIN = 200
INITIAL_PURCHASE_QTY_MAX = 1000

# 4) Auto-Nachkauf vor Verkauf (wenn Lager knapp)
RESTOCK_THRESHOLD   = 20
AUTORESTOCK_QTY_MIN = 200
AUTORESTOCK_QTY_MAX = 1000

# 5) Anzahl Bons pro Woche (pro Kunde)
RECEIPTS_PER_WEEK_MIN = 1
RECEIPTS_PER_WEEK_MAX = 7  # maximal 7 (Tage)

# 6) Regeln pro Kundentyp (einfach erklärt):
#    qty_*  → Stück pro Position (z. B. 1..25)
#    items_*→ Anzahl verschiedener Artikel im Bon (z. B. 1..25)
TYPE_RULES: Dict[str, Dict[str, int]] = {
    "Standard": {"qty_min": 1,  "qty_max": 25,  "items_min": 1,  "items_max": 25},
    "Silber"  : {"qty_min": 1,  "qty_max": 50,  "items_min": 1,  "items_max": 50},
    "Gold"    : {"qty_min": 5,  "qty_max": 100, "items_min": 5,  "items_max": 100},
    "Platin"  : {"qty_min": 10, "qty_max": 200, "items_min": 5,  "items_max": 200},
}

# 7) Fallback-Aufschlag, falls kein Listenpreis gefunden wurde
VK_FALLBACK_MARKUP = 1.35

# Wie oft Fortschritt drucken (alle N Tage)
PROGRESS_EVERY_N_DAYS = 7


# ============================== H I L F S F U N K T I O N E N ==============================

def daterange(d0: date, d1: date):
    """Einfacher Generator: gibt jeden Tag von d0 bis d1 zurück."""
    cur = d0
    while cur <= d1:
        yield cur
        cur += timedelta(days=1)


def rand_time_in_day(d: date) -> datetime:
    """Erzeugt eine zufällige Uhrzeit innerhalb der Öffnungszeiten für Datum d."""
    h = random.randint(STORE_OPEN_HOUR, STORE_CLOSE_HOUR - 1)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return datetime(d.year, d.month, d.day, h, m, s)


def fetch_all(conn, sql: str, params: Tuple = ()) -> List[dict]:
    """SQL ausführen und alle Zeilen als Liste von Dicts zurückgeben."""
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def fetch_one(conn, sql: str, params: Tuple = ()) -> Optional[dict]:
    """SQL ausführen und eine Zeile als Dict zurückgeben (oder None)."""
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def exec_one(conn, sql: str, params: Tuple = ()) -> None:
    """Einen SQL-Befehl (einmal) ausführen (INSERT/UPDATE/DELETE)."""
    with conn.cursor() as cur:
        cur.execute(sql, params)


def exec_many(conn, sql: str, rows: List[Tuple]) -> None:
    """Viele Zeilen auf einmal einfügen (schneller)."""
    if not rows:
        return
    with conn.cursor() as cur:
        cur.executemany(sql, rows)


def last_id(conn) -> int:
    """Letzte erzeugte ID (AUTO_INCREMENT) holen."""
    with conn.cursor() as cur:
        cur.execute("SELECT LAST_INSERT_ID();")
        return int(cur.fetchone()[0])


# ============================== C A C H E  /  N A C H S C H L A G E ==============================

def load_articles(conn) -> List[int]:
    """Alle artikelID als Liste."""
    rows = fetch_all(conn, "SELECT artikelID FROM artikel;")
    return [int(r["artikelID"]) for r in rows]


def load_kunden_with_type(conn) -> List[dict]:
    """
    Kunden mit Typ und Rabatt laden.
    Felder: kundenID, kundentypID, type_name, rabatt
    """
    sql = """
      SELECT k.kundenID,
             k.kundentypID,
             COALESCE(kt.bezeichnung,'Standard') AS type_name,
             COALESCE(kt.kundenrabatt,0)        AS rabatt
      FROM kunden k
      LEFT JOIN kundentyp kt ON kt.kundentypID = k.kundentypID
    """
    return fetch_all(conn, sql)


def load_suppliers_map(conn) -> Dict[int, List[Tuple[int, float]]]:
    """
    Map für Lieferanten pro Artikel bauen.
    Ergebnis: { artikelID: [(lieferantID, einkaufspreis), ...] }
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
    Letzten (gültigen) Listenpreis je Artikel holen (MySQL 8 Window-Funktion).
    Wenn kein Preis existiert → später Fallback verwenden.
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


# ============================== L A G E R (Bestand & Durchschnittskosten) ==============================

def get_stock_and_avgcost(conn, artikel_id: int) -> Tuple[int, float]:
    """Lagerbestand und durchschnittskosten (Durchschnitt) eines Artikels holen."""
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
    Einkauf: Lager erhöhen und neuen Durchschnittspreis berechnen (gleitender Durchschnitt).
    Formel: (alter_wert + einkaufswert) / neue_menge
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
    """Verkauf: Lager vermindern (nicht negativ werden lassen)."""
    cur_qty, _ = get_stock_and_avgcost(conn, artikel_id)
    new_qty = max(0, cur_qty - qty)
    exec_one(conn, "UPDATE artikel SET lagerbestand=%s WHERE artikelID=%s;", (new_qty, artikel_id))


# ============================== E I N K Ä U F E ==============================

def create_purchase_header(conn, lieferant_id: int, when: datetime, note: str) -> int:
    """Kopfzeile für Einkauf anlegen (einkauf)."""
    exec_one(
        conn,
        "INSERT INTO einkauf (lieferantID, einkaufsdatum, rechnung, bemerkung) "
        "VALUES (%s, %s, %s, %s);",
        (lieferant_id, when, f"INV-{random.randint(10_000, 99_999)}", note),
    )
    return last_id(conn)


def add_purchase_items(conn, einkauf_id: int, items: List[Tuple[int, int, float]]) -> None:
    """
    Positionen zum Einkauf hinzufügen.
    items = [(artikelID, menge, preis), ...]
    Zusätzlich Lager & Durchschnitt aktualisieren.
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
    """
    Anfangs-Einkäufe an 1–3 Tagen (Startbestand aufbauen).
    Nimmt pro Tag zufällig einen großen Teil der Artikel.
    """
    days = list(daterange(INITIAL_PURCHASES_START, INITIAL_PURCHASES_END))
    if not days:
        return

    artikel_ids = list(suppliers_by_art.keys())
    if not artikel_ids:
        return

    for d in days:
        when = rand_time_in_day(d)
        random.shuffle(artikel_ids)
        # „chunk“ = Teilmenge der Artikel für diesen Tag
        chunk = artikel_ids[: max(10, len(artikel_ids) // 3)]

        # Plan je Lieferant: {lieferantID: [(artikelID, menge, preis), ...]}
        plan: Dict[int, List[Tuple[int, int, float]]] = {}
        for a_id in chunk:
            choices = suppliers_by_art.get(a_id) or []
            if not choices:
                continue
            sup_id, price = random.choice(choices)
            qty = random.randint(INITIAL_PURCHASE_QTY_MIN, INITIAL_PURCHASE_QTY_MAX)
            plan.setdefault(sup_id, []).append((a_id, qty, price))

        # je Lieferant einen Einkauf
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
    Prüft Lager: wenn zu wenig für den Verkauf → sofort davor automatisch nachkaufen.
    Einkauf wird ca. 5–40 Minuten vor dem Bon gebucht (realistischer Zeitstempel).
    """
    cur_qty, _ = get_stock_and_avgcost(conn, artikel_id)
    if cur_qty >= need_qty:
        return

    choices = suppliers_by_art.get(artikel_id) or []
    if not choices:
        return  # kein Lieferant für diesen Artikel → kein Auto-Nachkauf

    sup_id, price = random.choice(choices)
    qty = random.randint(AUTORESTOCK_QTY_MIN, AUTORESTOCK_QTY_MAX)
    when_purchase = when - timedelta(hours=1, minutes=random.randint(5, 40))

    eid = create_purchase_header(conn, sup_id, when_purchase, "Auto restock")
    add_purchase_items(conn, eid, [(artikel_id, qty, price)])


# ============================== V E R K Ä U F E ==============================

def create_sale_header(conn, kunden_id: int, when: datetime) -> int:
    """Kopfzeile für Verkauf (Bon) anlegen."""
    exec_one(conn, "INSERT INTO verkauf (kundenID, verkaufsdatum) VALUES (%s, %s);", (kunden_id, when))
    return last_id(conn)


def add_sale_items(conn,
                   verkauf_id: int,
                   rows: List[Tuple[int, int, float, float]],
                   do_stock_update: bool = True) -> None:
    """
    Verkaufs-Positionen einfügen.
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
    """Gibt zufällige Wochentage (0=Mo..6=So) zurück, an denen verkauft wird."""
    count = max(0, min(7, count))
    return sorted(random.sample(range(7), count))


def generate_sales(conn,
                   artikel_ids: List[int],
                   kunden: List[dict],
                   suppliers_by_art: Dict[int, List[Tuple[int, float]]],
                   price_cache: Dict[int, float]) -> None:
    """
    Erzeugt die täglichen Verkäufe für den ganzen Zeitraum.
    Nutzt:
      • TYPE_RULES (wie viele Positionen + Stück)
      • Rabatt aus kundentyp
      • Auto-Nachkauf bei Bedarf
    """
    if not artikel_ids or not kunden:
        return

    # Plan: für jede Woche und jeden Kunden
    # (year, week, kundenID) → Liste von Verkaufstagen [0..6]
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
        wd = wd - 1  # 0..6 (Mo..So)

        for k in kunden:
            k_id = int(k["kundenID"])
            typ_name = (k.get("type_name") or "Standard").strip()
            rabatt   = float(k.get("rabatt") or 0.0)

            # An diesem Wochentag für diesen Kunden ein Bon geplant?
            if schedule.get((y, w, k_id)) and wd in schedule[(y, w, k_id)]:
                rules = TYPE_RULES.get(typ_name, TYPE_RULES["Standard"])

                # Wie viele Positionen im Bon?
                items_n = random.randint(rules["items_min"], rules["items_max"])
                items_n = max(1, min(items_n, len(artikel_ids)))

                when = rand_time_in_day(cur_day)
                vk_id = create_sale_header(conn, k_id, when)

                # Zufällige Artikel auswählen
                chosen = random.sample(artikel_ids, items_n)
                rows: List[Tuple[int, int, float, float]] = []

                for a_id in chosen:
                    # Stückzahl pro Position
                    qty = random.randint(rules["qty_min"], rules["qty_max"])

                    # Vor Verkauf ggf. nachkaufen (wenn Bestand knapp)
                    try:
                        restock_if_needed(conn, a_id, max(RESTOCK_THRESHOLD, qty), suppliers_by_art, when)
                    except Exception:
                        # Fehler beim Auto-Nachkauf ignorieren (geht weiter)
                        pass

                    # Verkaufspreis:
                    # 1) ideal: Listenpreis aus Cache
                    # 2) sonst: Durchschnittskosten * Aufschlag
                    base_price = price_cache.get(a_id)
                    if base_price is None:
                        _, avgc = get_stock_and_avgcost(conn, a_id)
                        base_price = (avgc or 1.0) * VK_FALLBACK_MARKUP

                    vk_preis = round(base_price * (1.0 - rabatt / 100.0), 2)
                    rows.append((a_id, qty, vk_preis, rabatt))

                # Positionen eintragen + Lager verringern
                add_sale_items(conn, vk_id, rows)

        # Einmal pro Tag speichern (schneller)
        conn.commit()

        # Fortschritt zeigen
        if i % PROGRESS_EVERY_N_DAYS == 0 or i == total_days:
            print(f"  • committed day {i}/{total_days}: {cur_day.isoformat()}")


# ============================== H A U P T A B L A U F ==============================

def clear_all(conn) -> None:
    """Alle bisherigen Bewegungen löschen und Lager zurücksetzen."""
    exec_one(conn, "DELETE FROM verkaufartikel;")
    exec_one(conn, "DELETE FROM verkauf;")
    exec_one(conn, "DELETE FROM einkaufartikel;")
    exec_one(conn, "DELETE FROM einkauf;")
    exec_one(conn, "UPDATE artikel SET lagerbestand=0, durchschnittskosten=NULL;")
    conn.commit()


def main() -> None:
    """Gesamtablauf: löschen → Nachschlage-Daten laden → Anfangseinkäufe → Verkäufe erzeugen."""
    conn = get_conn()
    if not conn:
        print("Keine Verbindung zur Datenbank")
        return

    try:
        # gleiche Zufallswerte bei jedem Lauf (reproduzierbar)
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
        # Manuell abgebrochen → aktuellen Tag zurückrollen
        conn.rollback()
        print("\n️ Stopped by user (Ctrl+C). Rolled back current transaction.")
    except Exception as e:
        # Fehler → alles zurückrollen
        conn.rollback()
        print(f" Fehler, Transaktion abgebrochen: {e}")
    finally:
        # Verbindung sicher schließen
        try:
            conn.close()
        except Exception:
            pass


# Startpunkt: nur ausführen, wenn direkt gestartet (nicht importiert)
if __name__ == "__main__":
    main()
