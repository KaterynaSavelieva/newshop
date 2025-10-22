USE newshopdb;

-- 🔹 Основні індекси для зв'язків
CREATE INDEX idx_kunden_kundentypID ON kunden(kundentypID);
CREATE INDEX idx_artikel_lieferantID ON artikellieferant(lieferantID);
CREATE INDEX idx_artikellieferant_artikelID ON artikellieferant(artikelID);
CREATE INDEX idx_einkauf_lieferantID ON einkauf(lieferantID);
CREATE INDEX idx_einkaufartikel_einkaufID ON einkaufartikel(einkaufID);
CREATE INDEX idx_einkaufartikel_artikelID ON einkaufartikel(artikelID);
CREATE INDEX idx_verkauf_kundenID ON verkauf(kundenID);
CREATE INDEX idx_verkaufartikel_verkaufID ON verkaufartikel(verkaufID);
CREATE INDEX idx_verkaufartikel_artikelID ON verkaufartikel(artikelID);
CREATE INDEX idx_artikelpreis_artikelID ON artikelpreis(artikelID);

-- 🔹 Додаткові для частих пошуків
CREATE INDEX idx_kunden_name ON kunden(nachname, vorname);
CREATE INDEX idx_lieferanten_name ON lieferanten(lieferant);
CREATE INDEX idx_artikel_name ON artikel(produktname);


CREATE INDEX idx_verkauf_datum ON verkauf(verkaufsdatum);



