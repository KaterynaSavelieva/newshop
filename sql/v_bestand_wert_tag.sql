USE newshopdb;

CREATE OR REPLACE VIEW v_bestand_tag AS
SELECT
    DATE(v.verkaufsdatum) AS tag,
    a.artikelID,
    a.produktname,
    a.lagerbestand AS bestand,
    a.durchschnittskosten AS ek_preis,
    ROUND(a.lagerbestand * COALESCE(a.durchschnittskosten,0), 2) AS lagerwert
FROM artikel a
LEFT JOIN verkaufartikel va ON va.artikelID = a.artikelID
LEFT JOIN verkauf v ON v.verkaufID = va.verkaufID
GROUP BY tag, a.artikelID
ORDER BY tag DESC, a.artikelID;

SELECT * FROM v_bestand_tag 
-- where lagerwert  
-- ORDER BY bestand DESC
;