USE newshopdb;

CREATE OR REPLACE VIEW v_sales_by_day AS
SELECT
  DATE(verkaufsdatum)                           AS tag,          
  COUNT(*)                                      AS positionen,
  SUM(menge)                                    AS menge, 
  ROUND(SUM(rabatt_eur), 2)                     AS rabatt_eur, 
  ROUND(SUM(umsatz), 2)                         AS umsatz,
  ROUND(SUM(umsatz_brutto), 2)                  AS umsatz_brutto, 
  ROUND(SUM(kosten), 2)                         AS kosten,
  ROUND(SUM(marge), 2)                          AS marge,
  -- ROUND(SUM(menge * vk_preis), 2)               AS umsatz_brutto,
  ROUND(SUM(marge_brutto), 2)                   AS marge_brutto, 
  ROUND(100 * SUM(marge) / NULLIF(SUM(umsatz), 0), 2)          AS marge_prozent,
  ROUND(100 * SUM(marge_brutto) / NULLIF(SUM(menge * vk_preis), 0), 2) AS marge_brutto_prozent 
FROM v_sales
GROUP BY DATE(verkaufsdatum)
ORDER BY tag DESC;

SELECT * FROM v_sales_by_day ORDER BY tag DESC;

SELECT *
FROM v_sales_by_day
WHERE tag BETWEEN '2024-10-01' AND '2025-10-31'
ORDER BY tag;

