from datetime import date, timedelta

# 🔹 Gibt einen SQL-Ausdruck für die Gruppierung nach Datum zurück.
#    grp: 'day' | 'month' | 'year'
#    column: Spaltenname (z. B. 'verkaufsdatum')
def f_group_expr(grp: str, column: str) -> str:
    grp = (grp or "day").lower()
    if grp == "month":
        return f"DATE_FORMAT({column}, '%%Y-%%m')"  # Beispiel: 2025-11
    elif grp == "quarter":
        return f"CONCAT(YEAR({column}), '-Q', QUARTER({column}))" #  YYYY-Qn: 2025-Q4)
    elif grp == "year":
        return f"DATE_FORMAT({column}, '%%Y')"      # Beispiel: 2025
    else:
        return f"DATE({column})"                    # Beispiel: 2025-11-01


# 🔹 Erstellt eine kurze Textliste der ausgewählten Elemente.
#    Wird im Bericht unter "Gefiltert → ..." verwendet.
def f_labels_for(selected_ids, pairs, limit: int = 6) -> str:
    if not selected_ids or not pairs:
        return ""
    # IDs den Namen zuordnen
    id_to_label = {str(pid): lbl for pid, lbl in pairs}
    # Nur Namen behalten, die existieren
    names = [id_to_label.get(str(x)) for x in selected_ids if str(x) in id_to_label]
    names = [n for n in names if n]  # Schutz gegen None
    if not names:
        return ""
    # Wenn die Anzahl klein ist → alles anzeigen
    if len(names) <= limit:
        return ", ".join(names)
    # Sonst: nur die ersten 6 + Anzahl der übrigen
    return ", ".join(names[:limit]) + f" … (+{len(names)-limit})"


# 🔹 Baut den WHERE-Teil eines SQL-Befehls und die Parameterliste.
#    Die Tabelle/VIEWS müssen Spalten haben:
#    verkaufsdatum, kundenID, kundentypID, artikelID
def f_build_where_sql(von: str, bis: str,
                    kunden_sel: list[str] | list = None,
                    kundentyp_sel: list[str] | list = None,
                    artikel_sel: list[str] | list = None) -> tuple[str, list]:
    # Leere Listen als Standard
    kunden_sel = kunden_sel or []
    kundentyp_sel = kundentyp_sel or []
    artikel_sel = artikel_sel or []

    # Oberes Datum exklusiv machen (bis + 1 Tag)
    bis_next = (date.fromisoformat(bis) + timedelta(days=1)).isoformat()

    where_sql = "verkaufsdatum >=%s AND verkaufsdatum <%s"
    params: list = [von, bis_next]

    # Wenn bestimmte Kunden ausgewählt sind
    if kunden_sel:
        where_sql += " AND kundenID IN (" + ",".join(["%s"] * len(kunden_sel)) + ")"
        params.extend(kunden_sel)

    # Wenn Kundentypen ausgewählt sind
    if kundentyp_sel:
        where_sql += " AND kundentypID IN (" + ",".join(["%s"] * len(kundentyp_sel)) + ")"
        params.extend(kundentyp_sel)

    # Wenn Artikel ausgewählt sind
    if artikel_sel:
        where_sql += " AND artikelID IN (" + ",".join(["%s"] * len(artikel_sel)) + ")"
        params.extend(artikel_sel)

    return where_sql, params
