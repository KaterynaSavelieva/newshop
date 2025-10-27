USE newshopdb;

CREATE OR REPLACE VIEW v_bestand_verlauf AS
SELECT
    d.datum,
    a.artikelID,
    a.produktname,
    COALESCE(a_start.lagerbestand, 0)
      + COALESCE((
          SELECT SUM(ea.einkaufsmenge)
          FROM einkaufartikel ea
          JOIN einkauf e ON e.einkaufID = ea.einkaufID
          WHERE ea.artikelID = a.artikelID
            AND DATE(e.einkaufsdatum) <= d.datum
        ), 0)
      - COALESCE((
          SELECT SUM(va.verkaufsmenge)
          FROM verkaufartikel va
          JOIN verkauf v ON v.verkaufID = va.verkaufID
          WHERE va.artikelID = a.artikelID
            AND DATE(v.verkaufsdatum) <= d.datum
        ), 0)
      AS bestand_tag
FROM artikel a
JOIN (
    SELECT DISTINCT DATE(verkaufsdatum) AS datum FROM verkauf
    UNION
    SELECT DISTINCT DATE(einkaufsdatum) AS datum FROM einkauf
) d
LEFT JOIN artikel a_start ON a_start.artikelID = a.artikelID
ORDER BY a.artikelID, d.datum;


SELECT * FROM v_bestand_verlauf WHERE bestand_tag <0;
