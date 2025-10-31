USE newshopdb;
-- що і скільки
SELECT e.einkaufID, e.lieferantID, e.einkaufsdatum, e.bemerkung, COUNT(ea.einkaufID) pos
FROM einkauf e
LEFT JOIN einkaufartikel ea ON ea.einkaufID = e.einkaufID
WHERE e.bemerkung LIKE 'Auto-fix stock '  
GROUP BY e.einkaufID;

-- видалити позиції цих закупок
DELETE ea FROM einkaufartikel ea
JOIN einkauf e ON e.einkaufID = ea.einkaufID
WHERE e.bemerkung LIKE 'Auto-fix stock ';

-- видалити заголовки без позицій
DELETE e FROM einkauf e
LEFT JOIN einkaufartikel ea ON ea.einkaufID = e.einkaufID
WHERE e.bemerkung LIKE 'Auto-fix stock ' AND ea.einkaufID IS NULL;
Auto-fix stock 

Auto-fix stock 