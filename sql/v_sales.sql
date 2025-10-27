CREATE OR REPLACE VIEW v_sales AS
SELECT
    v.verkaufsdatum                                        AS verkaufsdatum,
    k.kundenID                                             AS kundenID,
    CONCAT(k.vorname, ' ', k.nachname)                     AS kunde,
    kt.kundentypID                                         AS kundentypID,
    kt.bezeichnung                                         AS kundentyp,

    a.artikelID                                            AS artikelID,
    a.produktname                                          AS artikel,

    va.verkaufsmenge                                       AS menge,
    va.verkaufspreis                                       AS vk_preis,
    COALESCE(va.rabatt, 0)                                 AS rabatt_prozent,      
    COALESCE(a.durchschnittskosten, 0)                     AS ek_preis,       


    ROUND(va.verkaufsmenge * va.verkaufspreis * COALESCE(va.rabatt,0) / 100, 2)                 AS rabatt_eur,
    ROUND(va.verkaufsmenge * va.verkaufspreis * (1 - COALESCE(va.rabatt,0) / 100), 2)           AS umsatz,
	ROUND(va.verkaufsmenge * va.verkaufspreis, 2)            									AS umsatz_brutto,
    ROUND(va.verkaufsmenge * COALESCE(a.durchschnittskosten, 0), 2)                             AS kosten,
    ROUND( (va.verkaufsmenge * va.verkaufspreis * (1 - COALESCE(va.rabatt,0)/100))
         - (va.verkaufsmenge * COALESCE(a.durchschnittskosten,0)), 2)                           AS marge,
    ROUND( (va.verkaufsmenge * va.verkaufspreis)
         - (va.verkaufsmenge * COALESCE(a.durchschnittskosten,0)), 2)                           AS marge_brutto,


    ROUND(
        100 * (
            (va.verkaufsmenge * va.verkaufspreis * (1 - COALESCE(va.rabatt,0)/100))
          - (va.verkaufsmenge * COALESCE(a.durchschnittskosten,0))
        ) / NULLIF(va.verkaufsmenge * va.verkaufspreis * (1 - COALESCE(va.rabatt,0)/100), 0)
    , 2) 						AS marge_prozent,

    ROUND(
        100 * (
            (va.verkaufsmenge * va.verkaufspreis)
          - (va.verkaufsmenge * COALESCE(a.durchschnittskosten,0))
        ) / NULLIF(va.verkaufsmenge * va.verkaufspreis, 0)
    , 2) 							AS marge_brutto_prozent

FROM verkauf v
JOIN verkaufartikel  va ON v.verkaufID   = va.verkaufID
JOIN artikel         a  ON a.artikelID   = va.artikelID
JOIN kunden          k  ON k.kundenID    = v.kundenID
JOIN kundentyp       kt ON kt.kundentypID = k.kundentypID
;




SELECT * FROM v_sales;