# reports/service.py

def f_group_expr(grp: str, column: str) -> str:
    """
    Повертає SQL-вираз групування за датою (без параметрів).
    grp: 'day' | 'month' | 'year'
    column: назва колонки дати/часу (наприклад 'verkaufsdatum')
    """
    grp = (grp or "day").lower()
    if grp == "month":
        return f"DATE_FORMAT({column}, '%%Y-%%m')"
    elif grp == "year":
        return f"DATE_FORMAT({column}, '%%Y')"
    else:
        return f"DATE({column})"  # day


def f_labels_for(selected_ids, pairs, limit: int = 6) -> str:
    """
    Формує короткий рядок назв для блоку «Gefiltert → …».
    selected_ids: список вибраних id з request.args.getlist(...)
    pairs: список кортежів [(id, label), ...] із довідника
    """
    if not selected_ids or not pairs:
        return ""
    id_to_label = {str(pid): lbl for pid, lbl in pairs}
    names = [id_to_label.get(str(x)) for x in selected_ids if str(x) in id_to_label]
    names = [n for n in names if n]  # захист від None
    if not names:
        return ""
    if len(names) <= limit:
        return ", ".join(names)
    return ", ".join(names[:limit]) + f" … (+{len(names)-limit})"


def f_build_where_sql(von: str, bis: str,
                    kunden_sel: list[str] | list = None,
                    kundentyp_sel: list[str] | list = None,
                    artikel_sel: list[str] | list = None) -> tuple[str, list]:
    """
    Повертає (where_sql, params) для таблиці/в’ю з колонками:
    verkaufsdatum, kundenID, kundentypID, artikelID.
    """
    kunden_sel = kunden_sel or []
    kundentyp_sel = kundentyp_sel or []
    artikel_sel = artikel_sel or []

    where_sql = "verkaufsdatum BETWEEN %s AND %s"
    params: list = [von, bis]

    if kunden_sel:
        where_sql += " AND kundenID IN (" + ",".join(["%s"] * len(kunden_sel)) + ")"
        params.extend(kunden_sel)

    if kundentyp_sel:
        where_sql += " AND kundentypID IN (" + ",".join(["%s"] * len(kundentyp_sel)) + ")"
        params.extend(kundentyp_sel)

    if artikel_sel:
        where_sql += " AND artikelID IN (" + ",".join(["%s"] * len(artikel_sel)) + ")"
        params.extend(artikel_sel)

    return where_sql, params

