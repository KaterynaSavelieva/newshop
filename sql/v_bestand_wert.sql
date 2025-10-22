USE newshopdb;

CREATE OR REPLACE VIEW v_bestand_wert AS
SELECT
  a.artikelID,
  a.produktname,
  a.lagerbestand,
  a.durchschnittskosten,
  ROUND(a.lagerbestand * COALESCE(a.durchschnittskosten,0), 2) AS lagerwert
FROM artikel a
ORDER BY a.artikelID;

SELECT * FROM v_bestand_wert ORDER BY lagerwert DESC LIMIT 20;
