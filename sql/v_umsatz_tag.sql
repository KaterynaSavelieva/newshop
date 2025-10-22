USE newshopdb;

-- ЩОДЕННИЙ ПРОДАЖ (дохід, оцінка собівартості, маржа)
CREATE OR REPLACE VIEW v_umsatz_tag AS
SELECT
  DATE(v.verkaufsdatum)                              AS tag,
  ROUND(SUM(va.verkaufsmenge * va.verkaufspreis *
            (1 - va.rabatt/100)), 2)                 AS umsatz,
  ROUND(SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0)), 2)
                                                     AS kosten_schaetzung,
  ROUND(SUM(va.verkaufsmenge * va.verkaufspreis *
            (1 - va.rabatt/100)) -
        SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0)), 2)
                                                     AS deckungsbeitrag
FROM verkauf v
JOIN verkaufartikel va ON va.verkaufID = v.verkaufID
JOIN artikel a         ON a.artikelID   = va.artikelID
GROUP BY DATE(v.verkaufsdatum)
ORDER BY tag;

SELECT * FROM v_umsatz_tag WHERE tag >= CURDATE() - INTERVAL 30 DAY;
