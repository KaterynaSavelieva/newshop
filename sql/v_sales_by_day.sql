USE newshopdb;

CREATE OR REPLACE VIEW v_sales_by_day AS
SELECT
  DATE(verkaufsdatum)                           AS tag,               -- день
  COUNT(*)                                      AS positionen,        -- рядків продажу (позицій)
  SUM(menge)                                    AS menge,             -- штук
  ROUND(SUM(rabatt_eur), 2)                     AS rabatt_eur,        -- знижка, €
  ROUND(SUM(umsatz), 2)                         AS umsatz,            -- виручка NETTO (після знижки)
  ROUND(SUM(kosten), 2)                         AS kosten,            -- собівартість, €
  ROUND(SUM(marge), 2)                          AS marge,             -- маржа NETTO, €
  ROUND(SUM(menge * vk_preis), 2)               AS umsatz_brutto,     -- виручка BRUTTO (до знижки)
  ROUND(SUM(marge_brutto), 2)                   AS marge_brutto,      -- маржа BRUTTO, €
  ROUND(100 * SUM(marge) / NULLIF(SUM(umsatz), 0), 2)          AS marge_prozent,         -- % маржі нетто
  ROUND(100 * SUM(marge_brutto) / NULLIF(SUM(menge * vk_preis), 0), 2) AS marge_brutto_prozent  -- % маржі брутто
FROM v_sales
GROUP BY DATE(verkaufsdatum)
ORDER BY tag DESC;

SELECT * FROM v_sales_by_day ORDER BY tag DESC;

SELECT *
FROM v_sales_by_day
WHERE tag BETWEEN '2024-10-01' AND '2025-10-31'
ORDER BY tag;

