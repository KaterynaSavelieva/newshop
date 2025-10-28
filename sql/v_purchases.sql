-- Заготовка view для закупок
-- Таблиці припускаються такі:
--   einkauf (einkaufID, lieferantID, kaufdatum)
--   einkauf_artikel (einkaufID, artikelID, menge, ek_preis)
--   artikel (artikelID, produktname)
--   lieferanten (lieferantID, name)
USE newshopdb;

CREATE OR REPLACE VIEW v_purchases AS
SELECT
  e.einkaufsdatum,
  e.lieferantID,
  l.lieferant,
  ea.artikelID,
  a.produktname          AS artikel,
  ea.einkaufsmenge,
  ea.einkaufspreis,
  (ea.einkaufsmenge * ea.einkaufspreis) AS kosten,
  a.durchschnittskosten
FROM einkauf e
JOIN einkaufartikel ea ON ea.einkaufID = e.einkaufID
JOIN artikel a          ON a.artikelID  = ea.artikelID
JOIN lieferanten l      ON l.lieferantID = e.lieferantID;


SELECT * FROM v_purchases;