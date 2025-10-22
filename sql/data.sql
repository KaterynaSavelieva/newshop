USE newshopdb;

-- 1) KUNDENTYP (4 шт.)
INSERT INTO kundentyp (bezeichnung, kundenrabatt) VALUES
('Standard', 0.00), ('Silber', 5.00), ('Gold', 10.00), ('Platin', 15.00);

-- 2) KUNDEN (30 шт.)
INSERT INTO kunden (vorname, nachname, email, telefon, kundentypID) VALUES
('Anna','Huber','anna.huber@example.com','+431111001',1),
('Markus','Müller','markus.mueller@example.com','+431111002',2),
('Petra','Leitner','petra.leitner@example.com','+431111003',3),
('Thomas','Weber','thomas.weber@example.com','+431111004',1),
('Sandra','Klein','sandra.klein@example.com','+431111005',2),
('Michael','Berger','michael.berger@example.com','+431111006',1),
('Julia','Wolf','julia.wolf@example.com','+431111007',3),
('Florian','Schmid','florian.schmid@example.com','+431111008',1),
('Nina','Hofmann','nina.hofmann@example.com','+431111009',2),
('Sebastian','Graf','sebastian.graf@example.com','+431111010',4),
('Tobias','Lang','tobias.lang@example.com','+431111011',3),
('Lisa','Bauer','lisa.bauer@example.com','+431111012',2),
('Katrin','Moser','katrin.moser@example.com','+431111013',1),
('Patrick','Koller','patrick.koller@example.com','+431111014',2),
('Eva','Pichler','eva.pichler@example.com','+431111015',3),
('David','Hofer','david.hofer@example.com','+431111016',1),
('Martina','Fuchs','martina.fuchs@example.com','+431111017',2),
('Stefan','Mayr','stefan.mayr@example.com','+431111018',3),
('Claudia','Schwarz','claudia.schwarz@example.com','+431111019',1),
('Gerhard','Wagner','gerhard.wagner@example.com','+431111020',4),
('Renate','Kraus','renate.kraus@example.com','+431111021',1),
('Dominik','Brandl','dominik.brandl@example.com','+431111022',3),
('Vanessa','Hauser','vanessa.hauser@example.com','+431111023',2),
('Daniel','Egger','daniel.egger@example.com','+431111024',2),
('Johanna','Boehm','johanna.boehm@example.com','+431111025',3),
('Matthias','Lechner','matthias.lechner@example.com','+431111026',1),
('Ulrike','Roth','ulrike.roth@example.com','+431111027',4),
('Christian','Langer','christian.langer@example.com','+431111028',2),
('Angelika','Seidl','angelika.seidl@example.com','+431111029',1),
('Wolfgang','Reiter','wolfgang.reiter@example.com','+431111030',3);

-- 3) LIEFERANTEN (30 шт.)
INSERT INTO lieferanten (lieferant, kontaktperson, telefon, email) VALUES
('AlphaTrade GmbH','Sabine Huber','+4315551001','office@alphatrade.at'),
('BetaLogistik OG','Markus Leitner','+4315551002','kontakt@betalogi.at'),
('GammaSupply KG','Petra Auer','+4315551003','info@gammasupply.at'),
('DeltaImport e.U.','Thomas Krüger','+4315551004','support@deltaimport.at'),
('EpsilonGroßhandel','Julia Novak','+4315551005','sales@epsilon.at'),
('ZetaDistribution','Michael Berger','+4315551006','office@zeta.at'),
('OmegaHandel','Anna Hofer','+4315551007','kontakt@omegahandel.at'),
('PrimeSource','Nina Steiner','+4315551008','info@primesource.at'),
('RapidTrade','Christian Lang','+4315551009','sales@rapidtrade.at'),
('NordLogistik','Florian Graf','+4315551010','kontakt@nordlog.at'),
('ViennaSupply','Bettina Schwarz','+4315551011','info@viennasupply.at'),
('LinzHandel','Dominik Kern','+4315551012','office@linzhandel.at'),
('GrazDepot','Helga Wolf','+4315551013','verkauf@grazdepot.at'),
('InnsbruckImport','Patrick Bauer','+4315551014','office@ibkimport.at'),
('KlagenfurtTrade','Martina Ebner','+4315551015','support@kltrade.at'),
('SalzburgSource','Peter Fink','+4315551016','office@salzburgsource.at'),
('StPoltenSupply','Verena Mayer','+4315551017','sales@stpsupply.at'),
('EisenstadtPartner','David Hofer','+4315551018','office@eispartner.at'),
('MurauDepot','Lisa Roth','+4315551019','info@murau.at'),
('SteiermarkLogistik','Claudia Berger','+4315551020','kontakt@stmlog.at'),
('TirolTrade','Hannes Kurz','+4315551021','office@tiroltrade.at'),
('VorarlbergSupply','Lea König','+4315551022','sales@vlsupply.at'),
('CarinthiaImport','Martin Koch','+4315551023','info@carimport.at'),
('BurgenlandGroß','Sabine Leitner','+4315551024','office@bgross.at'),
('DonauDistribution','Paul Steiner','+4315551025','kontakt@donau.at'),
('WienNord','Stefan Haas','+4315551026','office@wiennord.at'),
('OstWestHandel','Erika Unger','+4315551027','info@ostwest.at'),
('EuroSupply','Rene March','+4315551028','sales@eurosupply.at'),
('CentralLog','Mona Beck','+4315551029','kontakt@centrallog.at'),
('SüdPartner','Harald Berg','+4315551030','office@suedpartner.at');

-- 4) ARTIKEL (30 шт.)
INSERT INTO artikel (produktname, lagerbestand, durchschnittskosten) VALUES
('Apfel', 50, 0.60),('Brot', 40, 1.20),('Milch', 30, 0.90),('Butter', 25, 2.10),
('Käse', 20, 2.50),('Eier', 100, 0.30),('Zucker', 60, 1.10),('Mehl', 80, 0.70),
('Reis', 70, 1.80),('Nudeln', 90, 1.50),('Tomaten', 45, 1.60),('Gurken', 35, 1.40),
('Zwiebeln', 40, 0.90),('Kartoffeln', 100, 0.50),('Öl', 30, 2.80),
('Essig', 25, 1.90),('Saft', 30, 2.50),('Wasser', 120, 0.40),
('Schokolade', 50, 2.30),('Kaffee', 20, 4.20),('Tee', 25, 3.50),
('Bier', 40, 1.80),('Wein', 25, 5.00),('Salz', 60, 0.80),
('Pfeffer', 40, 1.10),('Kekse', 70, 2.00),('Chips', 60, 1.60),
('Ketchup', 45, 2.10),('Senf', 40, 1.50),('Joghurt', 30, 1.00);

-- 5) ARTIKELPREIS (30 шт., поточні прайси)
INSERT INTO artikelpreis (artikelID, listenpreis, gueltig_ab, gueltig_bis) VALUES
(1,0.80,'2025-01-01',NULL),(2,1.50,'2025-01-01',NULL),(3,1.00,'2025-01-01',NULL),
(4,2.20,'2025-01-01',NULL),(5,2.90,'2025-01-01',NULL),(6,0.40,'2025-01-01',NULL),
(7,1.20,'2025-01-01',NULL),(8,0.90,'2025-01-01',NULL),(9,2.00,'2025-01-01',NULL),
(10,1.80,'2025-01-01',NULL),(11,2.00,'2025-01-01',NULL),(12,1.50,'2025-01-01',NULL),
(13,1.00,'2025-01-01',NULL),(14,0.70,'2025-01-01',NULL),(15,3.00,'2025-01-01',NULL),
(16,2.10,'2025-01-01',NULL),(17,2.80,'2025-01-01',NULL),(18,0.50,'2025-01-01',NULL),
(19,3.20,'2025-01-01',NULL),(20,4.50,'2025-01-01',NULL),(21,3.50,'2025-01-01',NULL),
(22,2.40,'2025-01-01',NULL),(23,5.50,'2025-01-01',NULL),(24,1.00,'2025-01-01',NULL),
(25,1.40,'2025-01-01',NULL),(26,2.60,'2025-01-01',NULL),(27,2.00,'2025-01-01',NULL),
(28,2.50,'2025-01-01',NULL),(29,1.80,'2025-01-01',NULL),(30,1.20,'2025-01-01',NULL);

-- 6) ARTIKELLIEFERANT (≥30 зв’язків)
INSERT INTO artikellieferant (lieferantID, artikelID, einkaufspreis) VALUES
(1,1,0.50),(1,2,1.00),(1,3,0.70),
(2,4,1.80),(2,5,2.10),(2,6,0.20),
(3,7,0.90),(3,8,0.60),(3,9,1.40),
(4,10,1.20),(4,11,1.30),
(5,12,1.00),(5,13,0.70),(5,14,0.40),
(6,15,2.20),(6,16,1.50),
(7,17,2.00),(7,18,0.30),
(8,19,2.10),(8,20,3.50),
(9,21,2.80),(9,22,1.50),
(10,23,4.00),(10,24,0.60),
(11,25,0.90),(11,26,1.80),
(12,27,1.30),(13,28,1.70),
(14,29,1.10),(15,30,0.90);

-- 7) EINKAUF (30 заголовків, різні постачальники)
INSERT INTO einkauf (lieferantID, einkaufsdatum, rechnung, bemerkung) VALUES
(1,NOW()-INTERVAL 30 DAY,'INV-1001','Erstbestellung'),
(2,NOW()-INTERVAL 29 DAY,'INV-1002',''),
(3,NOW()-INTERVAL 28 DAY,'INV-1003',''),
(4,NOW()-INTERVAL 27 DAY,'INV-1004',''),
(5,NOW()-INTERVAL 26 DAY,'INV-1005',''),
(6,NOW()-INTERVAL 25 DAY,'INV-1006',''),
(7,NOW()-INTERVAL 24 DAY,'INV-1007',''),
(8,NOW()-INTERVAL 23 DAY,'INV-1008',''),
(9,NOW()-INTERVAL 22 DAY,'INV-1009',''),
(10,NOW()-INTERVAL 21 DAY,'INV-1010',''),
(11,NOW()-INTERVAL 20 DAY,'INV-1011',''),
(12,NOW()-INTERVAL 19 DAY,'INV-1012',''),
(13,NOW()-INTERVAL 18 DAY,'INV-1013',''),
(14,NOW()-INTERVAL 17 DAY,'INV-1014',''),
(15,NOW()-INTERVAL 16 DAY,'INV-1015',''),
(16,NOW()-INTERVAL 15 DAY,'INV-1016',''),
(17,NOW()-INTERVAL 14 DAY,'INV-1017',''),
(18,NOW()-INTERVAL 13 DAY,'INV-1018',''),
(19,NOW()-INTERVAL 12 DAY,'INV-1019',''),
(20,NOW()-INTERVAL 11 DAY,'INV-1020',''),
(21,NOW()-INTERVAL 10 DAY,'INV-1021',''),
(22,NOW()-INTERVAL 9 DAY,'INV-1022',''),
(23,NOW()-INTERVAL 8 DAY,'INV-1023',''),
(24,NOW()-INTERVAL 7 DAY,'INV-1024',''),
(25,NOW()-INTERVAL 6 DAY,'INV-1025',''),
(26,NOW()-INTERVAL 5 DAY,'INV-1026',''),
(27,NOW()-INTERVAL 4 DAY,'INV-1027',''),
(28,NOW()-INTERVAL 3 DAY,'INV-1028',''),
(29,NOW()-INTERVAL 2 DAY,'INV-1029',''),
(30,NOW()-INTERVAL 1 DAY,'INV-1030','Letzte Lieferung');

-- 8) EINKAUFARTIKEL (по 3 позиції на кожен закуп — 90 рядків)
INSERT INTO einkaufartikel (einkaufID, artikelID, einkaufsmenge, einkaufspreis) VALUES
-- 1..10
(1,1,40,0.50),(1,2,30,1.00),(1,3,30,0.70),
(2,4,20,1.85),(2,5,15,2.15),(2,6,50,0.20),
(3,7,30,0.92),(3,8,40,0.62),(3,9,25,1.42),
(4,10,50,1.22),(4,11,35,1.28),(4,12,30,1.00),
(5,13,40,0.68),(5,14,60,0.40),(5,15,20,2.18),
(6,16,25,1.52),(6,17,20,2.02),(6,18,80,0.30),
(7,19,25,2.12),(7,20,15,3.45),(7,21,20,2.78),
(8,22,30,1.48),(8,23,12,3.95),(8,24,40,0.58),
(9,25,30,0.88),(9,26,25,1.78),(9,27,35,1.28),
(10,28,20,1.68),(10,29,25,1.10),(10,30,30,0.88),
-- 11..20
(11,1,30,0.51),(11,5,10,2.12),(11,9,20,1.39),
(12,2,20,1.02),(12,6,40,0.21),(12,10,25,1.19),
(13,14,30,0.41),(13,18,60,0.30),(13,22,25,1.49),
(14,3,20,0.72),(14,7,25,0.91),(14,11,20,1.30),
(15,15,20,2.21),(15,19,20,2.11),(15,23,10,3.98),
(16,4,20,1.82),(16,8,30,0.61),(16,12,20,0.99),
(17,16,15,1.51),(17,20,10,3.46),(17,24,30,0.59),
(18,13,20,0.69),(18,17,20,2.01),(18,21,15,2.79),
-- 21..30
(19,25,20,0.89),(19,29,15,1.09),(19,30,20,0.89),
(20,26,20,1.79),(20,28,15,1.69),(20,27,25,1.29),
(21,1,20,0.52),(21,2,15,1.01),(21,3,15,0.71),
(22,4,15,1.84),(22,5,10,2.14),(22,6,30,0.20),
(23,7,20,0.93),(23,8,25,0.61),(23,9,15,1.41),
(24,10,30,1.21),(24,11,20,1.29),(24,12,20,1.00),
(25,13,25,0.69),(25,14,40,0.40),(25,15,15,2.19),
(26,16,20,1.50),(26,17,15,2.00),(26,18,50,0.30),
(27,19,20,2.11),(27,20,10,3.44),(27,21,15,2.77),
(28,22,20,1.47),(28,23,10,3.96),(28,24,25,0.59),
(29,25,20,0.89),(29,26,20,1.79),(29,27,20,1.29),
(30,28,15,1.68),(30,29,15,1.10),(30,30,20,0.88);

-- 9) VERKAUF (30 заголовків)
INSERT INTO verkauf (kundenID, verkaufsdatum) VALUES
(1,NOW()-INTERVAL 20 DAY),(2,NOW()-INTERVAL 19 DAY),(3,NOW()-INTERVAL 18 DAY),
(4,NOW()-INTERVAL 17 DAY),(5,NOW()-INTERVAL 16 DAY),(6,NOW()-INTERVAL 15 DAY),
(7,NOW()-INTERVAL 14 DAY),(8,NOW()-INTERVAL 13 DAY),(9,NOW()-INTERVAL 12 DAY),
(10,NOW()-INTERVAL 11 DAY),(11,NOW()-INTERVAL 10 DAY),(12,NOW()-INTERVAL 9 DAY),
(13,NOW()-INTERVAL 8 DAY),(14,NOW()-INTERVAL 7 DAY),(15,NOW()-INTERVAL 6 DAY),
(16,NOW()-INTERVAL 5 DAY),(17,NOW()-INTERVAL 4 DAY),(18,NOW()-INTERVAL 3 DAY),
(19,NOW()-INTERVAL 2 DAY),(20,NOW()-INTERVAL 1 DAY),
(21,NOW()-INTERVAL 20 HOUR),(22,NOW()-INTERVAL 18 HOUR),
(23,NOW()-INTERVAL 16 HOUR),(24,NOW()-INTERVAL 14 HOUR),
(25,NOW()-INTERVAL 12 HOUR),(26,NOW()-INTERVAL 10 HOUR),
(27,NOW()-INTERVAL 8 HOUR),(28,NOW()-INTERVAL 6 HOUR),
(29,NOW()-INTERVAL 4 HOUR),(30,NOW()-INTERVAL 2 HOUR);

-- 10) VERKAUFARTIKEL (по 3 позиції на продаж — 90 рядків)
INSERT INTO verkaufartikel (verkaufID, artikelID, verkaufsmenge, verkaufspreis, rabatt) VALUES
-- 1..10
(1,1,5,0.80,0),(1,2,3,1.50,5),(1,3,4,1.00,0),
(2,4,2,2.20,0),(2,5,1,2.90,10),(2,6,10,0.40,0),
(3,7,5,1.20,0),(3,8,2,0.90,0),(3,9,3,2.00,5),
(4,10,4,1.80,0),(4,11,3,2.00,0),(4,12,2,1.50,0),
(5,13,2,1.00,0),(5,14,3,0.70,0),(5,15,1,3.00,5),
(6,16,2,2.10,0),(6,17,1,2.80,0),(6,18,6,0.50,0),
(7,19,2,3.20,0),(7,20,1,4.50,10),(7,21,2,3.50,0),
(8,22,3,2.40,0),(8,23,1,5.50,10),(8,24,4,1.00,0),
(9,25,3,1.40,0),(9,26,2,2.60,0),(9,27,2,2.00,0),
(10,28,2,2.50,0),(10,29,2,1.80,0),(10,30,3,1.20,0),
-- 11..20
(11,1,4,0.80,0),(11,5,1,2.90,5),(11,9,2,2.00,0),
(12,2,2,1.50,0),(12,6,12,0.40,0),(12,10,3,1.80,0),
(13,14,4,0.70,0),(13,18,8,0.50,0),(13,22,3,2.40,0),
(14,3,3,1.00,0),(14,7,4,1.20,0),(14,11,2,2.00,0),
(15,15,1,3.00,5),(15,19,2,3.20,0),(15,23,1,5.50,10),
(16,4,2,2.20,0),(16,8,3,0.90,0),(16,12,2,1.50,0),
(17,16,2,2.10,0),(17,20,1,4.50,10),(17,24,4,1.00,0),
(18,13,3,1.00,0),(18,17,2,2.80,0),(18,21,2,3.50,0),
-- 21..30
(19,25,2,1.40,0),(19,29,2,1.80,0),(19,30,3,1.20,0),
(20,26,2,2.60,0),(20,28,2,2.50,0),(20,27,2,2.00,0),
(21,1,3,0.80,0),(21,2,2,1.50,0),(21,3,2,1.00,0),
(22,4,2,2.20,0),(22,5,1,2.90,10),(22,6,8,0.40,0),
(23,7,3,1.20,0),(23,8,2,0.90,0),(23,9,2,2.00,5),
(24,10,3,1.80,0),(24,11,2,2.00,0),(24,12,2,1.50,0),
(25,13,2,1.00,0),(25,14,3,0.70,0),(25,15,1,3.00,5),
(26,16,2,2.10,0),(26,17,1,2.80,0),(26,18,5,0.50,0),
(27,19,2,3.20,0),(27,20,1,4.50,10),(27,21,2,3.50,0),
(28,22,3,2.40,0),(28,23,1,5.50,10),(28,24,3,1.00,0),
(29,25,2,1.40,0),(29,26,2,2.60,0),(29,27,2,2.00,0),
(30,28,2,2.50,0),(30,29,2,1.80,0),(30,30,3,1.20,0);
