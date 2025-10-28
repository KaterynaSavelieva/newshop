USE newshopdb;

CREATE OR REPLACE VIEW v_bestand_wert AS
SELECT
    a.artikelID,
    a.produktname,
    a.lagerbestand,
    ROUND(COALESCE(a.durchschnittskosten, 0),2) AS durchschnittskosten,
    ROUND(a.lagerbestand * COALESCE(a.durchschnittskosten, 0), 2) AS lagerwert,
    MIN(al.einkaufspreis) AS min_preis,
    MAX(al.einkaufspreis) AS max_preis
FROM artikel a
JOIN artikellieferant al ON al.artikelID=a.artikelID
GROUP BY a.artikelID, a.produktname, a.lagerbestand, a.durchschnittskosten
ORDER BY artikelID
-- ORDER BY lagerwert DESC
;


SELECT * FROM v_bestand_wert ORDER BY artikelID
-- LIMIT 20
;
