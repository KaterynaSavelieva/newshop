USE newshopdb;
SELECT verkauf.*, verkaufartikel.*
FROM verkauf JOIN verkaufartikel ON	verkauf.verkaufID=verkaufartikel.verkaufID
ORDER BY verkaufartikel.verkaufID DESC;

SELECT lieferanten.lieferant, artikel.produktname, einkauf.*, einkaufartikel.*
FROM einkauf 
JOIN einkaufartikel ON einkauf.einkaufID=einkaufartikel.einkaufID 
JOIN artikel ON artikel.artikelID=einkaufartikel.artikelID 
JOIN lieferanten ON lieferanten.lieferantID=einkauf.lieferantID
-- WHERE einkauf.lieferantID=10
-- WHERE einkaufartikel.artikelID=24
ORDER BY einkaufartikel.einkaufID DESC;



