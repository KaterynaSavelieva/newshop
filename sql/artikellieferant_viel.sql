SELECT artikelID, COUNT(*) AS anzahl_lieferanten,
       MIN(einkaufspreis) AS min_preis,
       MAX(einkaufspreis) AS max_preis
FROM artikellieferant
GROUP BY artikelID
ORDER BY artikelID;

   
INSERT INTO artikellieferant (lieferantID, artikelID, einkaufspreis)
SELECT t.new_lieferantID, t.artikelID, ROUND(t.new_einkaufspreis, 2)
FROM (
    SELECT 
        a.artikelID,
        al.lieferantID 						AS orig_lieferantID,
        al.einkaufspreis 					AS base_einkaufspreis,
        CASE WHEN al.lieferantID + 1 > 30 
			 THEN al.lieferantID + 1 - 30 
             ELSE al.lieferantID + 1 END 	AS new_lieferantID,
        al.einkaufspreis * 0.93 			AS new_einkaufspreis
    FROM artikel a
    JOIN artikellieferant al ON al.artikelID = a.artikelID
    WHERE al.lieferantID IS NOT NULL
    UNION ALL
    SELECT 
        a.artikelID,
        al.lieferantID 						AS orig_lieferantID,
        al.einkaufspreis 					AS base_einkaufspreis,
        CASE WHEN al.lieferantID + 2 > 30 
			 THEN al.lieferantID + 2 - 30 
             ELSE al.lieferantID + 2 END 	AS new_lieferantID,
        al.einkaufspreis * 1.08 			AS new_einkaufspreis
    FROM artikel a
    JOIN artikellieferant al ON al.artikelID = a.artikelID
    WHERE al.lieferantID IS NOT NULL
) t
LEFT JOIN artikellieferant x 
  ON x.lieferantID = t.new_lieferantID AND x.artikelID = t.artikelID
WHERE x.lieferantID IS NULL
ORDER BY t.artikelID;

