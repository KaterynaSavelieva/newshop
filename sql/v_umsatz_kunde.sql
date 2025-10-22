USE newshopdb;

-- Загальний підсумок по клієнту
CREATE OR REPLACE VIEW v_umsatz_kunde AS
SELECT
  k.kundenID,
  k.vorname,
  k.nachname,
  COUNT(DISTINCT v.verkaufID)                                                 AS bestellungen,
  ROUND(SUM(va.verkaufsmenge * va.verkaufspreis * (1 - va.rabatt/100)), 2)   AS umsatz,
  ROUND(SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0)), 2)        AS kosten_schaetzung,
  ROUND(SUM(va.verkaufsmenge * va.verkaufspreis * (1 - va.rabatt/100)) -
        SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0)), 2)        AS deckungsbeitrag
FROM kunden k
JOIN verkauf v         ON v.kundenID = k.kundenID
JOIN verkaufartikel va ON va.verkaufID = v.verkaufID
JOIN artikel a         ON a.artikelID   = va.artikelID
GROUP BY k.kundenID, k.vorname, k.nachname;

-- За останні 90 днів
CREATE OR REPLACE VIEW v_umsatz_kunde_90 AS
SELECT
  k.kundenID,
  k.vorname,
  k.nachname,
  COUNT(DISTINCT v.verkaufID)                                                 AS bestellungen,
  ROUND(SUM(va.verkaufsmenge * va.verkaufspreis * (1 - va.rabatt/100)), 2)   AS umsatz,
  ROUND(SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0)), 2)        AS kosten_schaetzung,
  ROUND(SUM(va.verkaufsmenge * va.verkaufspreis * (1 - va.rabatt/100)) -
        SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0)), 2)        AS deckungsbeitrag
FROM kunden k
JOIN verkauf v         ON v.kundenID = k.kundenID
JOIN verkaufartikel va ON va.verkaufID = v.verkaufID
JOIN artikel a         ON a.artikelID   = va.artikelID
WHERE v.verkaufsdatum >= NOW() - INTERVAL 90 DAY
GROUP BY k.kundenID, k.vorname, k.nachname;

-- Топ-10 клієнтів за 90 днів за виторгом
SELECT * FROM v_umsatz_kunde_90 ORDER BY umsatz
-- 
DESC LIMIT 10
 ;

-- Топ-10 клієнтів за весь час за маржею
SELECT * FROM v_umsatz_kunde ORDER BY deckungsbeitrag
-- 
DESC LIMIT 10
;
