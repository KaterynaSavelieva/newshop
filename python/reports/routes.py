#   Reports-Modul
# Dieses Modul enthält alle Routen (Seiten) für Berichte unter /reports/…

from flask import Blueprint, render_template, request
from flask_login import login_required
from ..db import get_conn
from .service import (
    f_group_expr,     # baut SQL-Ausdruck für Gruppierung nach Tag/Monat/Jahr/Quartal
    f_labels_for,     # wandelt ausgewählte IDs in kurze Namenliste für "Gefiltert → …"
    f_build_where_sql,# baut WHERE-Teil + Parameter je nach Filtern und Zeitraum
    f_get_period,     # liest von/bis aus URL oder nimmt Standard (z. B. letzte 30 Tage)
    f_get_filters     # liest Listen von ausgewählten IDs (kunden, artikel, kundentypen)
)


#  Blueprint für alle Report-Seiten (alle URLs beginnen mit /reports/)
# Ein Blueprint ist wie ein "Mini-App-Modul": wir sammeln thematisch passende
# Routen zusammen (hier: Reports) und registrieren sie später im Haupt-Flask-App.
reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


# Bericht: Tages-, Monats- oder Jahresübersicht
# URL: /reports/daily?von=YYYY-MM-DD&bis=YYYY-MM-DD&grp=day|month|year
@reports_bp.get("/daily")
@login_required  # Seite nur für eingeloggte Benutzer
def report_daily():
    # Zeitraum lesen (Standard: letzte 30 Tage bis heute).
    # f_get_period(30) liefert ein Tupel (von, bis) als ISO-Datum.
    von, bis = f_get_period(30)

    # Gruppierung: 'day'/'month'/'year' (kommt aus URL-Parameter ?grp=…)
    grp = request.args.get("grp", "day")

    #  Filter aus der URL: mehrere Kunden/Artikel/Kundentypen sind möglich.
    # Ergebnis: drei Listen mit IDs (Strings).
    kunden_sel, artikel_sel, kundentyp_sel = f_get_filters()

    rows, totals = [], {}
    #  Verbindung zur Datenbank holen
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            #  Stammdaten (Listen) laden, damit die Filter-Dropdowns in der UI
            # Namen statt IDs zeigen können.
            cur.execute("""
                SELECT kundenID, CONCAT(vorname,' ',nachname) AS kunde
                FROM kunden
                ORDER BY kunde
            """)
            kunden_list = cur.fetchall()

            cur.execute("""
                SELECT kundentypID, bezeichnung AS typ
                FROM kundentyp
                ORDER BY typ
            """)
            kundentyp_list = cur.fetchall()

            cur.execute("""
                SELECT artikelID, produktname AS artikel
                FROM artikel
                ORDER BY artikel
            """)
            artikel_list = cur.fetchall()

            #  WHERE-Teil + Parameter dynamisch bauen
            where_sql, params = f_build_where_sql(
                von, bis, kunden_sel, kundentyp_sel, artikel_sel
            )

            # 🏷 SQL-Ausdruck für Gruppierung wählen (DATE(), DATE_FORMAT(…))
            label_expr = f_group_expr(grp, "verkaufsdatum")

            #  Daten aus Sicht v_sales laden und zusammenfassen
            cur.execute(
                f"""
                SELECT
                  {label_expr} AS tag,                          -- 0 Zeitlabel
                  COUNT(*)     AS positionen,                   -- 1 Anzahl Zeilen
                  SUM(menge)   AS menge,                        -- 2 Menge gesamt
                  ROUND(SUM(rabatt_eur), 2)          AS rabatt_eur,       -- 3
                  ROUND(SUM(umsatz), 2)              AS umsatz,           -- 4
                  ROUND(SUM(kosten), 2)              AS kosten,           -- 5
                  ROUND(SUM(marge), 2)               AS marge,            -- 6
                  ROUND(SUM(umsatz_brutto), 2)       AS umsatz_brutto,    -- 7
                  ROUND(SUM(marge_brutto), 2)        AS marge_brutto,     -- 8
                  ROUND(100 * SUM(marge) / NULLIF(SUM(umsatz), 0), 2)            AS marge_prozent,        -- 9
                  ROUND(100 * SUM(marge_brutto) / NULLIF(SUM(umsatz_brutto), 0), 2) AS marge_brutto_prozent -- 10
                FROM v_sales
                WHERE {where_sql}
                GROUP BY {label_expr}
                ORDER BY {label_expr}
                """,
                params
            )
            rows = cur.fetchall()
        # 🔒 Verbindung sauber schließen
        conn.close()

    #  Gesamtsummen über alle Zeilen berechnen (für Fußzeile/Kacheln)
    if rows:
        totals = {
            "positionen": sum(r[1] for r in rows),
            "menge":      float(sum(r[2] for r in rows)),
            "rabatt_eur": float(sum(r[3] for r in rows)),
            "umsatz":     float(sum(r[4] for r in rows)),
            "kosten":     float(sum(r[5] for r in rows)),
            "marge":      float(sum(r[6] for r in rows)),
            "umsatz_br":  float(sum(r[7] for r in rows)),
            "marge_br":   float(sum(r[8] for r in rows)),
        }
    else:
        # Kein Ergebnis → alles auf Null setzen (verhindert Fehler im Template)
        totals = {
            "positionen": 0, "menge": 0.0, "rabatt_eur": 0.0,
            "umsatz": 0.0, "kosten": 0.0, "marge": 0.0,
            "umsatz_br": 0.0, "marge_br": 0.0
        }

    #  Lesbare Filter-Zeile zusammenbauen („Gefiltert → …“)
    kunden_txt    = f_labels_for(kunden_sel,    locals().get("kunden_list", []))
    kundentyp_txt = f_labels_for(kundentyp_sel, locals().get("kundentyp_list", []))
    artikel_txt   = f_labels_for(artikel_sel,   locals().get("artikel_list", []))

    parts = [f"von: {von}", f"bis: {bis}", f"Intervall: {grp}"]
    if kunden_txt:    parts.append(f"Kunde: {kunden_txt}")
    if kundentyp_txt: parts.append(f"Kundentyp: {kundentyp_txt}")
    if artikel_txt:   parts.append(f"Artikel: {artikel_txt}")
    filter_line = "Gefiltert → " + " · ".join(parts)

    # HTML-Template mit Daten füllen
    return render_template(
        "reports_daily.html",
        title=f"Umsatz pro {grp}",
        rows=rows, totals=totals,
        von=von, bis=bis, grp=grp,
        kunden_list=locals().get("kunden_list", []),
        artikel_list=locals().get("artikel_list", []),
        kundentyp_list=locals().get("kundentyp_list", []),
        kunden_sel=kunden_sel, artikel_sel=artikel_sel, kundentyp_sel=kundentyp_sel,
        filter_line=filter_line,
    )



# Top-Kunden nach Umsatz
# URL: /reports/customers?top=20&von=…&bis=… (Filter analog)
@reports_bp.get("/customers")
@login_required
def report_customers():
    # Zeitraum: Standard letzte 30 Tage
    von, bis = f_get_period(30)

    # Filter-IDs (Mehrfachauswahl)
    kunden_sel, artikel_sel, kundentyp_sel = f_get_filters()

    # Sicherstellen, dass top_n in sinnvollem Bereich bleibt
    try:
        top_n = int(request.args.get("top", "20"))
    except ValueError:
        top_n = 20
    top_n = max(5, min(top_n, 100))

    rows, totals = [], {}
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # Stammlisten (für Filter in der UI)
            cur.execute("""
                SELECT kundenID, CONCAT(vorname,' ',nachname) AS kunde
                FROM kunden
                ORDER BY kunde
            """)
            kunden_list = cur.fetchall()

            cur.execute("""
                SELECT kundentypID, bezeichnung AS typ
                FROM kundentyp
                ORDER BY typ
            """)
            kundentyp_list = cur.fetchall()

            cur.execute("""
                SELECT artikelID, produktname AS artikel
                FROM artikel
                ORDER BY artikel
            """)
            artikel_list = cur.fetchall()

            # WHERE und Parameter
            where_sql, params = f_build_where_sql(
                von, bis, kunden_sel, kundentyp_sel, artikel_sel
            )

            # Aggregation pro Kunde (absteigend nach Umsatz)
            sql = f"""
                SELECT
                  kundenID,
                  kunde,
                  COUNT(*)                            AS positionen,
                  SUM(menge)                          AS menge,
                  ROUND(SUM(umsatz), 2)               AS umsatz,
                  ROUND(SUM(kosten), 2)               AS kosten,
                  ROUND(SUM(umsatz) - SUM(kosten), 2) AS marge,
                  ROUND(
                    100 * (SUM(umsatz) - SUM(kosten)) / NULLIF(SUM(umsatz), 0), 2
                  ) AS marge_prozent
                FROM v_sales
                WHERE {where_sql}
                GROUP BY kundenID, kunde
                ORDER BY umsatz DESC
                LIMIT {top_n}
            """
            cur.execute(sql, params)
            rows = cur.fetchall()
        conn.close()

    # Summen für Fußzeile
    if rows:
        totals = {
            "positionen": sum(r[2] for r in rows),
            "menge":      float(sum(r[3] for r in rows)),
            "umsatz":     float(sum(r[4] for r in rows)),
            "kosten":     float(sum(r[5] for r in rows)),
            "marge":      float(sum(r[6] for r in rows)),
        }
    else:
        totals = {"positionen": 0, "menge": 0.0, "umsatz": 0.0, "kosten": 0.0, "marge": 0.0}

    # Lesbare „Gefiltert → …“-Zeile
    kunden_txt    = f_labels_for(kunden_sel,    locals().get("kunden_list", []))
    kundentyp_txt = f_labels_for(kundentyp_sel, locals().get("kundentyp_list", []))
    artikel_txt   = f_labels_for(artikel_sel,   locals().get("artikel_list", []))

    parts = [f"von: {von}", f"bis: {bis}", f"Top: {top_n}"]
    if kunden_txt:    parts.append(f"Kunde: {kunden_txt}")
    if kundentyp_txt: parts.append(f"Kundentyp: {kundentyp_txt}")
    if artikel_txt:   parts.append(f"Artikel: {artikel_txt}")
    filter_line = "Gefiltert → " + " · ".join(parts)

    return render_template(
        "reports_customers.html",
        title="Umsatz pro Kunde",
        rows=rows, totals=totals,
        von=von, bis=bis, top_n=top_n,
        kunden_list=locals().get("kunden_list", []),
        artikel_list=locals().get("artikel_list", []),
        kundentyp_list=locals().get("kundentyp_list", []),
        kunden_sel=kunden_sel, artikel_sel=artikel_sel, kundentyp_sel=kundentyp_sel,
        filter_line=filter_line,
    )


#  Artikel-Report oder Zeitreihe für EINEN Artikel
# URL: /reports/articles?grp=items|day|month|year
@reports_bp.get("/articles")
@login_required
def report_articles():
    # Zeitraum: letzte 30 Tage
    von, bis = f_get_period(30)

    # Filter-IDs
    kunden_sel, artikel_sel, kundentyp_sel = f_get_filters()

    # Modus:
    #   - "items": Top-Artikel nach Umsatz
    #   - "day"/"month"/"year": Zeitreihe (nur wenn GENAU ein Artikel gewählt ist)
    grp = request.args.get("grp", "items")

    # Top-N Begrenzung
    try:
        top_n = int(request.args.get("top", "20"))
    except ValueError:
        top_n = 20
    top_n = max(5, min(top_n, 100))

    rows, totals = [], {}
    ts_mode_msg = None  # Hinweistext, falls Zeitreihe ohne Einzelwahl versucht wird

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # Stammlisten
            cur.execute("SELECT artikelID, produktname FROM artikel ORDER BY produktname")
            artikel_list = cur.fetchall()

            cur.execute("SELECT kundenID, CONCAT(vorname,' ',nachname) FROM kunden ORDER BY 2")
            kunden_list = cur.fetchall()

            cur.execute("SELECT kundentypID, bezeichnung FROM kundentyp ORDER BY bezeichnung")
            kundentyp_list = cur.fetchall()

            # WHERE aufbauen
            where_sql, params = f_build_where_sql(
                von, bis, kunden_sel, kundentyp_sel, artikel_sel
            )

            if grp == "items":
                # Top-Artikel nach Umsatz
                sql = f"""
                    SELECT
                      artikelID,
                      artikel,
                      COUNT(*)             AS positionen,
                      SUM(menge)           AS menge,
                      ROUND(SUM(umsatz),2) AS umsatz,
                      ROUND(SUM(kosten),2) AS kosten,
                      ROUND(SUM(marge),2)  AS marge,
                      ROUND(100*SUM(marge)/NULLIF(SUM(umsatz),0),2) AS marge_prozent
                    FROM v_sales
                    WHERE {where_sql}
                    GROUP BY artikelID, artikel
                    ORDER BY umsatz DESC
                    LIMIT {top_n}
                """
                cur.execute(sql, params)
                rows = cur.fetchall()
            else:
                # Zeitreihe benötigt genau EINEN Artikel
                if len(artikel_sel) != 1:
                    ts_mode_msg = "Bitte genau einen Artikel wählen, um einen Zeitverlauf anzuzeigen."
                else:
                    label_expr = f_group_expr(grp, "verkaufsdatum")
                    sql = f"""
                        SELECT
                          {label_expr}                    AS label,
                          COUNT(*)                        AS positionen,
                          SUM(menge)                      AS menge,
                          ROUND(SUM(umsatz),2)            AS umsatz,
                          ROUND(SUM(kosten),2)            AS kosten,
                          ROUND(SUM(marge),2)             AS marge,
                          ROUND(100*SUM(marge)/NULLIF(SUM(umsatz),0),2) AS marge_prozent
                        FROM v_sales
                        WHERE {where_sql}
                          AND artikelID = %s
                        GROUP BY label
                        ORDER BY label
                    """
                    params_ts = params + [artikel_sel[0]]
                    cur.execute(sql, params_ts)
                    rows = cur.fetchall()
        conn.close()

    #  Gesamtsummen korrekt je Modus
    if rows:
        # Indexe je nach SELECT-Form
        pos_idx    = 2 if grp == "items" else 1
        menge_idx  = 3 if grp == "items" else 2
        umsatz_idx = 4 if grp == "items" else 3
        kosten_idx = 5 if grp == "items" else 4
        marge_idx  = 6 if grp == "items" else 5
        totals = {
            "positionen": sum(r[pos_idx] for r in rows),
            "menge":      float(sum(r[menge_idx] for r in rows)),
            "umsatz":     float(sum(r[umsatz_idx] for r in rows)),
            "kosten":     float(sum(r[kosten_idx] for r in rows)),
            "marge":      float(sum(r[marge_idx]  for r in rows)),
        }
    else:
        totals = {"positionen": 0, "menge": 0.0, "umsatz": 0.0, "kosten": 0.0, "marge": 0.0}

    # Lesbare Filterzeile
    artikel_txt   = f_labels_for(artikel_sel,   locals().get("artikel_list", []))
    kunden_txt    = f_labels_for(kunden_sel,    locals().get("kunden_list", []))
    kundentyp_txt = f_labels_for(kundentyp_sel, locals().get("kundentyp_list", []))

    parts = [f"von: {von}", f"bis: {bis}", f"Modus: {'Artikel' if grp=='items' else grp}"]
    if artikel_txt:   parts.append(f"Artikel: {artikel_txt}")
    if kunden_txt:    parts.append(f"Kunde: {kunden_txt}")
    if kundentyp_txt: parts.append(f"Kundentyp: {kundentyp_txt}")
    filter_line = "Gefiltert → " + " · ".join(parts)

    return render_template(
        "reports_articles.html",
        title="Umsatz pro Artikel",
        rows=rows, totals=totals,
        von=von, bis=bis, top_n=top_n, grp=grp,
        artikel_list=locals().get("artikel_list", []),
        kunden_list=locals().get("kunden_list", []),
        kundentyp_list=locals().get("kundentyp_list", []),
        artikel_sel=artikel_sel, kunden_sel=kunden_sel, kundentyp_sel=kundentyp_sel,
        filter_line=filter_line, ts_mode_msg=ts_mode_msg,
    )


# Lagerwarnung (niedriger Bestand)
# URL: /reports/stock_low?limit=1000
@reports_bp.get("/stock_low")
@login_required
def report_stock_low():
    # Schwellwert aus Parametern (Fallback 1000)
    threshold = request.args.get("limit", "1000")
    try:
        threshold = int(threshold)
    except ValueError:
        threshold = 1000

    rows = []
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # Einfache Liste: alle Artikel unterhalb der Schwelle
            cur.execute(
                """
                SELECT
                  artikelID,
                  produktname AS artikel,
                  lagerbestand,
                  %s AS schwelle,
                  lagerbestand - %s AS differenz
                FROM artikel
                WHERE lagerbestand < %s
                ORDER BY lagerbestand ASC
                """,
                (threshold, threshold, threshold)
            )
            rows = cur.fetchall()
        conn.close()

    return render_template(
        "reports_stock_low.html",
        title="Lagerwarnung / Artikel mit niedrigem Bestand",
        rows=rows, threshold=threshold
    )


#  Lagerumschlag 90 Tage (für JavaScript-Charts/Tabellen)
# URL: /reports/turnover
import json

@reports_bp.get("/turnover")
@login_required
def report_turnover():
    rows = []
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            # Werte aus vorbereiteter Sicht v_umschlag_90tage:
            # enthält Bestände, Durchschnittskosten, COGS 90, Umschlag u. a.
            cur.execute("""
                SELECT
                    artikelID,          -- 0
                    produktname,        -- 1
                    lagerbestand,       -- 2
                    durchschnittskosten,-- 3
                    lagerwert_now,      -- 4
                    min_einkaufspreis,  -- 5
                    max_einkaufspreis,  -- 6
                    verkaufsmenge_90,   -- 7
                    cogs_90,            -- 8
                    umschlag_90_approx, -- 9
                    lagerdauer_tage     -- 10
                FROM v_umschlag_90tage
                ORDER BY umschlag_90_approx ASC, lagerdauer_tage ASC
            """)
            rows = cur.fetchall()
        conn.close()

    # Für das Frontend in ein JSON-freundliches Format bringen
    rows_dict = [
        {
            "artikelID": r[0],
            "artikel": r[1],
            "bestand": int(r[2]),
            "dkost": float(r[3] or 0),
            "lagerwert": float(r[4] or 0),
            "ek_min": float(r[5] or 0),
            "ek_max": float(r[6] or 0),
            "vk90": float(r[7] or 0),
            "cogs90": float(r[8] or 0),
            "umschlag": float(r[9] or 0),
            "lagerdauer": float(r[10] or 0),
        }
        for r in rows
    ]

    return render_template(
        "reports_turnover.html",
        title="Umschlag 90 Tage",
        rows=rows,                      # optional auch als Jinja-Tabelle nutzbar
        rows_json=json.dumps(rows_dict) # Hauptdaten für JS
    )


# ️ Pareto 80/20 (Umsatz oder Marge)
# URL: /reports/pareto?by=artikel|kunde&k=umsatz|marge&von=…&bis=…
@reports_bp.get("/pareto")
@login_required
def report_pareto():
    # Zeitraum (Standard: letzte 90 Tage)
    von, bis = f_get_period(90)

    # Dimension: nach Artikel oder Kunde gruppieren?
    by = request.args.get("by", "artikel")  # 'artikel' | 'kunde'
    # Kennzahl: Umsatz oder Marge betrachten?
    k  = request.args.get("k", "umsatz")    # 'umsatz' | 'marge'

    # Metrik absichern
    k = k.lower()
    if k not in ("umsatz", "marge"):
        k = "umsatz"

    # SQL-Spalte für Aggregation definieren + lesbare Beschriftung
    metric_col   = "SUM(umsatz)" if k == "umsatz" else "SUM(marge)"
    metric_label = "Umsatz (€)"   if k == "umsatz" else "Marge (€)"
    page_title   = f"Pareto 80/20 – {metric_label} pro {'Artikel' if by=='artikel' else 'Kunde'}"

    # SQL je nach Dimension zusammenstellen
    if by == "kunde":
        sql = f"""
            SELECT
                kundenID   AS id,
                kunde      AS name,
                ROUND({metric_col}, 2) AS metric
            FROM v_sales
            WHERE verkaufsdatum >= %s AND verkaufsdatum <= %s
            GROUP BY kundenID, kunde
            ORDER BY metric DESC
        """
    else:
        sql = f"""
            SELECT
                artikelID  AS id,
                artikel    AS name,
                ROUND({metric_col}, 2) AS metric
            FROM v_sales
            WHERE verkaufsdatum >= %s AND verkaufsdatum <= %s
            GROUP BY artikelID, artikel
            ORDER BY metric DESC
        """

    rows = []
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute(sql, (von, bis))
            # Ergebnis ist Liste von Tupeln: (id, name, metric)
            rows = cur.fetchall()
        conn.close()

    # Anteil je Zeile und kumulierten Anteil berechnen
    total = float(sum(r[2] for r in rows)) or 1.0
    data, cum, top80_count = [], 0.0, 0
    for i, (rid, name, val) in enumerate(rows, start=1):
        value = float(val)
        share = (value / total) * 100.0
        cum += share
        d = {
            "rank": i,                 # Rangplatz
            "id": rid,                 # Primärschlüssel
            "name": name,              # Anzeigename
            "value": round(value, 2),  # Wert (Umsatz oder Marge)
            "share": round(share, 2),  # Anteil in %
            "cum_share": round(cum, 2),# kumulativer Anteil in %
            "in80": cum <= 80.0        # True, solange kumulativ ≤ 80 %
        }
        data.append(d)
        if d["in80"]:
            top80_count = i  # wie viele Einträge bilden die 80 %

    total_items = len(data)
    top80_pct = round((top80_count / total_items) * 100, 1) if total_items else 0.0

    # Für das Chart nur die ersten 25 Einträge (besser lesbar)
    chart_labels   = [d["name"] for d in data[:25]]
    chart_bars     = [d["value"] for d in data[:25]]
    chart_cum_line = [d["cum_share"] for d in data[:25]]

    return render_template(
        "reports_pareto.html",
        title=page_title,
        by=by, von=von, bis=bis,
        k=k,                       # gewählte Kennzahl (umsatz/marge)
        metric_label=metric_label, # Text in Legende/Überschrift
        total=round(total, 2),
        top80_count=top80_count,
        top80_pct=top80_pct,
        rows=data,                 # Tabelle
        chart_labels=chart_labels, # X-Achse der Balken
        chart_bars=chart_bars,     # Werte (Balken)
        chart_cum_line=chart_cum_line, # kumulative % (Linie)
    )
