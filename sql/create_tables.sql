USE newshopdb;
/*DROP TABLE IF EXISTS artikelpreis;
DROP TABLE IF EXISTS verkauf_artikel;
DROP TABLE IF EXISTS verkauf;
DROP TABLE IF EXISTS verkaufartikel;
DROP TABLE IF EXISTS einkaufartikel;
DROP TABLE IF EXISTS artikellieferant;
DROP TABLE IF EXISTS verkauf;
DROP TABLE IF EXISTS einkauf;
DROP TABLE IF EXISTS artikel;
DROP TABLE IF EXISTS kunden;
DROP TABLE IF EXISTS lieferanten;
DROP TABLE IF EXISTS kundentyp;*/

CREATE TABLE kundentyp (
  kundentypID INT AUTO_INCREMENT PRIMARY KEY,
  bezeichnung VARCHAR(50) NOT NULL,
  kundenrabatt DECIMAL(5,2) NOT NULL DEFAULT 0
);

CREATE TABLE kunden (
  kundenID INT AUTO_INCREMENT PRIMARY KEY,
  vorname VARCHAR(50) NOT NULL,
  nachname VARCHAR(50) NOT NULL,
  email VARCHAR(100) UNIQUE,
  telefon VARCHAR(20),
  kundentypID INT,
  FOREIGN KEY (kundentypID) REFERENCES kundentyp(kundentypID)
);

CREATE TABLE lieferanten (
  lieferantID INT AUTO_INCREMENT PRIMARY KEY,
  lieferant VARCHAR(100) NOT NULL,
  kontaktperson VARCHAR(100),
  telefon VARCHAR(20),
  email VARCHAR(100)
);

CREATE TABLE artikel (
  artikelID INT AUTO_INCREMENT PRIMARY KEY,
  produktname VARCHAR(100) NOT NULL,
  lagerbestand INT DEFAULT 0,
  durchschnittskosten DECIMAL(10,4) NULL  -- середня собівартість
);

CREATE TABLE artikellieferant (
  lieferantID INT NOT NULL,
  artikelID INT NOT NULL,
  einkaufspreis DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (lieferantID, artikelID),
  FOREIGN KEY (lieferantID) REFERENCES lieferanten(lieferantID),
  FOREIGN KEY (artikelID) REFERENCES artikel(artikelID)
);

CREATE TABLE einkauf (
  einkaufID INT AUTO_INCREMENT PRIMARY KEY,
  lieferantID INT NOT NULL,
  einkaufsdatum DATETIME DEFAULT CURRENT_TIMESTAMP,
  rechnung VARCHAR(50),
  bemerkung VARCHAR(255),
  FOREIGN KEY (lieferantID) REFERENCES lieferanten(lieferantID)
);

CREATE TABLE einkaufartikel (
  einkauf_artikelID INT AUTO_INCREMENT PRIMARY KEY,
  einkaufID INT NOT NULL,
  artikelID INT NOT NULL,
  einkaufsmenge INT CHECK (einkaufsmenge > 0),
  einkaufspreis DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (einkaufID) REFERENCES einkauf(einkaufID),
  FOREIGN KEY (artikelID) REFERENCES artikel(artikelID)
);

CREATE TABLE verkauf (
  verkaufID INT AUTO_INCREMENT PRIMARY KEY,
  kundenID INT NOT NULL,
  verkaufsdatum DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (kundenID) REFERENCES kunden(kundenID)
);

CREATE TABLE verkaufartikel (
  verkauf_artikelID INT AUTO_INCREMENT PRIMARY KEY,
  verkaufID INT NOT NULL,
  artikelID INT NOT NULL,
  verkaufsmenge INT CHECK (verkaufsmenge > 0),
  verkaufspreis DECIMAL(10,2) NOT NULL,
  rabatt DECIMAL(5,2) NOT NULL DEFAULT 0,
  FOREIGN KEY (verkaufID) REFERENCES verkauf(verkaufID),
  FOREIGN KEY (artikelID) REFERENCES artikel(artikelID)
);

CREATE TABLE artikelpreis (
  preisID INT AUTO_INCREMENT PRIMARY KEY,
  artikelID INT NOT NULL,
  listenpreis DECIMAL(10,2) NOT NULL,
  gueltig_ab DATE NOT NULL,
  gueltig_bis DATE NULL,
  FOREIGN KEY (artikelID) REFERENCES artikel(artikelID)
);