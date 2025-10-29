# python/reports/routes.py
from datetime import date, timedelta
from flask import Blueprint, render_template, request
from flask_login import login_required
from ..db import get_conn
from .service import f_group_expr, f_labels_for, f_build_where_sql

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.get("/daily")
@login_required
def report_daily():
    bis = request.args.get("bis") or date.today().isoformat()
    von = request.args.get("von") or (date.fromisoformat(bis) - timedelta(days=30)).isoformat()
    grp = request.args.get("grp", "day")

    kunden_sel    = request.args.getlist("kunden")
    artikel_sel   = request.args.getlist("artikel")
    kundentyp_sel = request.args.getlist("kundentypen")

    rows, totals = [], {}
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT kundenID, CONCAT(vorname,' ',nachname) AS kunde FROM kunden ORDER BY kunde")
            kunden_list = cur.fetchall()
            cur.execute("SELECT kundentypID, bezeichnung AS typ FROM kundentyp ORDER BY typ")
            kundentyp_list = cur.fetchall()
            cur.execute("SELECT artikelID, produktname AS artikel FROM artikel ORDER BY artikel")
            artikel_list = cur.fetchall()

            where_sql, params = f_build_where_sql(von, bis, kunden_sel, kundentyp_sel, artikel_sel)
            label_expr = f_group_expr(grp, "verkaufsdatum")

            cur.execute(
                f"""
                SELECT
                  {label_expr} AS tag,
                  COUNT(*)     AS positionen,
                  SUM(menge)   AS menge,
                  ROUND(SUM(rabatt_eur), 2)          AS rabatt_eur,
                  ROUND(SUM(umsatz), 2)              AS umsatz,
                  ROUND(SUM(kosten), 2)              AS kosten,
                  ROUND(SUM(marge), 2)               AS marge,
                  ROUND(SUM(umsatz_brutto), 2)       AS umsatz_brutto,
                  ROUND(SUM(marge_brutto), 2)        AS marge_brutto,
                  ROUND(100 * SUM(marge) / NULLIF(SUM(umsatz), 0), 2)            AS marge_prozent,
                  ROUND(100 * SUM(marge_brutto) / NULLIF(SUM(umsatz_brutto), 0), 2) AS marge_brutto_prozent
                FROM v_sales
                WHERE {where_sql}
                GROUP BY {label_expr}
                ORDER BY {label_expr}
                """,
                params
            )
            rows = cur.fetchall()
        conn.close()

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
        totals = {"positionen":0,"menge":0.0,"rabatt_eur":0.0,"umsatz":0.0,"kosten":0.0,"marge":0.0,"umsatz_br":0.0,"marge_br":0.0}

    kunden_txt    = f_labels_for(kunden_sel,    locals().get("kunden_list", []))
    kundentyp_txt = f_labels_for(kundentyp_sel, locals().get("kundentyp_list", []))
    artikel_txt   = f_labels_for(artikel_sel,   locals().get("artikel_list", []))

    parts = [f"von: {von}", f"bis: {bis}", f"Intervall: {grp}"]
    if kunden_txt:    parts.append(f"Kunde: {kunden_txt}")
    if kundentyp_txt: parts.append(f"Kundentyp: {kundentyp_txt}")
    if artikel_txt:   parts.append(f"Artikel: {artikel_txt}")
    filter_line = "Gefiltert → " + " · ".join(parts)

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


@reports_bp.get("/customers")
@login_required
def report_customers():
    bis = request.args.get("bis") or date.today().isoformat()
    von = request.args.get("von") or (date.fromisoformat(bis) - timedelta(days=30)).isoformat()

    kunden_sel    = request.args.getlist("kunden")
    artikel_sel   = request.args.getlist("artikel")
    kundentyp_sel = request.args.getlist("kundentypen")

    try:
        top_n = int(request.args.get("top", "20"))
    except ValueError:
        top_n = 20
    top_n = max(5, min(top_n, 100))

    rows, totals = [], {}
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT kundenID, CONCAT(vorname,' ',nachname) AS kunde FROM kunden ORDER BY kunde")
            kunden_list = cur.fetchall()
            cur.execute("SELECT kundentypID, bezeichnung AS typ FROM kundentyp ORDER BY typ")
            kundentyp_list = cur.fetchall()
            cur.execute("SELECT artikelID, produktname AS artikel FROM artikel ORDER BY artikel")
            artikel_list = cur.fetchall()

            where_sql, params = f_build_where_sql(von, bis, kunden_sel, kundentyp_sel, artikel_sel)

            sql = f"""
                SELECT
                  kundenID,
                  kunde,
                  COUNT(*)                            AS positionen,
                  SUM(menge)                          AS menge,
                  ROUND(SUM(umsatz), 2)               AS umsatz,
                  ROUND(SUM(kosten), 2)               AS kosten,
                  ROUND(SUM(umsatz) - SUM(kosten), 2) AS marge,
                  ROUND(100 * (SUM(umsatz) - SUM(kosten)) / NULLIF(SUM(umsatz), 0), 2) AS marge_prozent
                FROM v_sales
                WHERE {where_sql}
                GROUP BY kundenID, kunde
                ORDER BY umsatz DESC
                LIMIT {top_n}
            """
            cur.execute(sql, params)
            rows = cur.fetchall()
        conn.close()

    if rows:
        totals = {
            "positionen": sum(r[2] for r in rows),
            "menge":      float(sum(r[3] for r in rows)),
            "umsatz":     float(sum(r[4] for r in rows)),
            "kosten":     float(sum(r[5] for r in rows)),
            "marge":      float(sum(r[6] for r in rows)),
        }
    else:
        totals = {"positionen":0,"menge":0.0,"umsatz":0.0,"kosten":0.0,"marge":0.0}

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


@reports_bp.get("/articles")
@login_required
def report_articles():
    bis = request.args.get("bis") or date.today().isoformat()
    von = request.args.get("von") or (date.fromisoformat(bis) - timedelta(days=30)).isoformat()

    artikel_sel   = request.args.getlist("artikel")
    kunden_sel    = request.args.getlist("kunden")
    kundentyp_sel = request.args.getlist("kundentypen")
    grp = request.args.get("grp", "items")

    try:
        top_n = int(request.args.get("top", "20"))
    except ValueError:
        top_n = 20
    top_n = max(5, min(top_n, 100))

    rows, totals = [], {}
    ts_mode_msg = None

    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT artikelID, produktname FROM artikel ORDER BY produktname")
            artikel_list = cur.fetchall()
            cur.execute("SELECT kundenID, CONCAT(vorname,' ',nachname) FROM kunden ORDER BY 2")
            kunden_list = cur.fetchall()
            cur.execute("SELECT kundentypID, bezeichnung FROM kundentyp ORDER BY bezeichnung")
            kundentyp_list = cur.fetchall()

            where_sql, params = f_build_where_sql(von, bis, kunden_sel, kundentyp_sel, artikel_sel)

            if grp == "items":
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

    if rows:
        pos_idx   = 2 if grp == "items" else 1
        menge_idx = 3 if grp == "items" else 2
        umsatz_idx= 4 if grp == "items" else 3
        kosten_idx= 5 if grp == "items" else 4
        marge_idx = 6 if grp == "items" else 5
        totals = {
            "positionen": sum(r[pos_idx] for r in rows),
            "menge":      float(sum(r[menge_idx] for r in rows)),
            "umsatz":     float(sum(r[umsatz_idx] for r in rows)),
            "kosten":     float(sum(r[kosten_idx] for r in rows)),
            "marge":      float(sum(r[marge_idx]  for r in rows)),
        }
    else:
        totals = {"positionen":0,"menge":0.0,"umsatz":0.0,"kosten":0.0,"marge":0.0}

    artikel_txt   = f_labels_for(artikel_sel,   locals().get("artikel_list", []))
    kunden_txt    = f_labels_for(kunden_sel,    locals().get("kunden_list", []))
    kundentyp_txt = f_labels_for(kundentyp_sel, locals().get("kundentyp_list", []))

    parts=[f"von: {von}", f"bis: {bis}", f"Modus: {'Artikel' if grp=='items' else grp}"]
    if artikel_txt:   parts.append(f"Artikel: {artikel_txt}")
    if kunden_txt:    parts.append(f"Kunde: {kunden_txt}")
    if kundentyp_txt: parts.append(f"Kundentyp: {kundentyp_txt}")
    filter_line="Gefiltert → "+" · ".join(parts)

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

@reports_bp.get("/reports/stock_low")
@login_required
def report_stock_low():
    threshold = request.args.get("limit", "150")
    try:
        threshold = int(threshold)
    except ValueError:
        threshold = 150

    rows = []
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
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

# python/reports/routes.py
from flask import Blueprint, render_template, request
from flask_login import login_required
from ..db import get_conn

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.get("/turnover")
@login_required
def report_turnover():
    """
    Umschlag 90 Tage – дашборд оборотності складу.
    Бере дані з в’ю v_umschlag_90tage.
    """
    rows = []
    conn = get_conn()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    artikelID,
                    produktname,
                    lagerbestand,
                    durchschnittskosten,
                    lagerwert_now,
                    min_einkaufspreis,
                    max_einkaufspreis,
                    verkaufsmenge_90,
                    cogs_90,
                    umschlag_90_approx,
                    lagerdauer_tage
                FROM v_umschlag_90tage
                ORDER BY umschlag_90_approx DESC, lagerdauer_tage ASC;
            """)
            rows = cur.fetchall()
        conn.close()

    # для шапки/титулу
    return render_template(
        "reports_turnover.html",
        title="Umschlag 90 Tage",
        rows=rows
    )

