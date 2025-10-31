USE newshopdb;

-- 🔧 Вимикаємо тригери
SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0;
SET FOREIGN_KEY_CHECKS=0;

DROP TRIGGER IF EXISTS trg_einkaufartikel_ai;
DROP TRIGGER IF EXISTS trg_einkaufartikel_au;
DROP TRIGGER IF EXISTS trg_einkaufartikel_ad;

DROP TRIGGER IF EXISTS trg_verkaufartikel_bi;
DROP TRIGGER IF EXISTS trg_verkaufartikel_au;
DROP TRIGGER IF EXISTS trg_verkaufartikel_ad;

DROP TRIGGER IF EXISTS trg_update_avgcost;

SET SQL_NOTES=@OLD_SQL_NOTES;
SET FOREIGN_KEY_CHECKS=1;