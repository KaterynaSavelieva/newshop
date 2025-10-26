USE newshopdb;

CREATE OR REPLACE VIEW v_bestand_wert AS
SELECT
    a.artikelID,
    a.produktname,
    a.lagerbestand,
    COALESCE(a.durchschnittskosten, 0) AS durchschnittskosten,
    ROUND(a.lagerbestand * COALESCE(a.durchschnittskosten, 0), 2) AS lagerwert
FROM artikel a
ORDER BY lagerwert DESC;


SELECT * FROM v_bestand_wert ORDER BY lagerwert DESC 
-- LIMIT 20
;
