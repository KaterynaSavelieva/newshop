USE newshopdb;

-- 1) Порахуємо дефіцит у тимчасову таблицю
CREATE TEMPORARY TABLE tmp_need AS
SELECT
  va.artikelID,
  GREATEST(0, 3 * SUM(va.verkaufsmenge) - a.lagerbestand) AS need
FROM verkaufartikel va
JOIN verkauf v  ON v.verkaufID  = va.verkaufID
JOIN kunden  k  ON k.kundenID   = v.kundenID
JOIN artikel a  ON a.artikelID  = va.artikelID
WHERE v.verkaufsdatum >= '2025-01-01 00:00:00'
  AND v.verkaufsdatum <  '2025-10-26 00:00:00'
  AND k.kundentypID = 2
GROUP BY va.artikelID
HAVING need > 0;

-- 2) Просто докинемо залишок (якщо у тебе НІЯКІ тригери на artikel не забороняють)
UPDATE artikel a
JOIN tmp_need t ON t.artikelID = a.artikelID
SET a.lagerbestand = a.lagerbestand + t.need;

DROP TEMPORARY TABLE tmp_need;


SELECT va.*, v.*, k.kundentypID
FROM verkaufartikel va
JOIN verkauf v ON v.verkaufID=va.verkaufID
JOIN kunden k ON k.kundenID=v.kundenID
WHERE v.verkaufsdatum >= '2025-01-01 00:00:00'
	AND v.verkaufsdatum < '2025-10-26 00:00:00' 
    AND k.kundentypID = 2;
    


UPDATE verkaufartikel va
JOIN verkauf v  ON v.verkaufID = va.verkaufID
JOIN kunden  k  ON k.kundenID = v.kundenID
SET va.verkaufsmenge = va.verkaufsmenge * 3
WHERE v.verkaufsdatum >= '2025-01-01 00:00:00'
  AND v.verkaufsdatum <  '2025-10-26 00:00:00'
  AND k.kundentypID = 2;

SELECT * FROM kundentyp;