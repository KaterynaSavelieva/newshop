USE newshopdb;

/*
DROP TRIGGER IF EXISTS trg_einkaufartikel_ai;
DROP TRIGGER IF EXISTS trg_einkaufartikel_au;
DROP TRIGGER IF EXISTS trg_einkaufartikel_ad;

DROP TRIGGER IF EXISTS trg_verkaufartikel_bi;
DROP TRIGGER IF EXISTS trg_verkaufartikel_au;
DROP TRIGGER IF EXISTS trg_verkaufartikel_ad;
*/
DELIMITER $$

-- ЗАКУПІВЛІ (einkaufartikel)

-- AFTER INSERT: збільшуємо склад і перераховуємо середню собівартість (durchschnittskosten)
CREATE TRIGGER trg_einkaufartikel_ai
AFTER INSERT ON einkaufartikel
FOR EACH ROW
BEGIN
  DECLARE v_old_qty INT;
  DECLARE v_old_avg DECIMAL(10,4);
  DECLARE v_new_qty INT;
  DECLARE v_new_avg DECIMAL(10,4);
  DECLARE v_total_value DECIMAL(18,6);

  SELECT COALESCE(lagerbestand,0), COALESCE(durchschnittskosten,0)
    INTO v_old_qty, v_old_avg
  FROM artikel
  WHERE artikelID = NEW.artikelID;

  SET v_new_qty    = v_old_qty + NEW.einkaufsmenge;
  SET v_total_value = (v_old_qty * v_old_avg) + (NEW.einkaufsmenge * NEW.einkaufspreis);

  SET v_new_avg = CASE
                    WHEN v_new_qty > 0 THEN ROUND(v_total_value / v_new_qty, 4)
                    ELSE NULL
                  END;

  UPDATE artikel
     SET lagerbestand = v_new_qty,
         durchschnittskosten = v_new_avg
   WHERE artikelID = NEW.artikelID;
END $$

-- AFTER UPDATE: переобчислюємо, врахувавши зміну кількості/ціни саме цього рядка закупівлі
CREATE TRIGGER trg_einkaufartikel_au
AFTER UPDATE ON einkaufartikel
FOR EACH ROW
BEGIN
  DECLARE v_cur_qty INT;
  DECLARE v_cur_avg DECIMAL(10,4);
  DECLARE v_new_qty INT;
  DECLARE v_new_total DECIMAL(18,6);
  DECLARE v_new_avg DECIMAL(10,4);

  SELECT COALESCE(lagerbestand,0), COALESCE(durchschnittskosten,0)
    INTO v_cur_qty, v_cur_avg
  FROM artikel
  WHERE artikelID = NEW.artikelID;

  SET v_new_qty   = v_cur_qty - OLD.einkaufsmenge + NEW.einkaufsmenge;
  SET v_new_total = (v_cur_qty * v_cur_avg)
                    - (OLD.einkaufsmenge * OLD.einkaufspreis)
                    + (NEW.einkaufsmenge * NEW.einkaufspreis);

  SET v_new_avg = CASE
                    WHEN v_new_qty > 0 THEN ROUND(v_new_total / v_new_qty, 4)
                    ELSE NULL
                  END;

  UPDATE artikel
     SET lagerbestand = v_new_qty,
         durchschnittskosten = v_new_avg
   WHERE artikelID = NEW.artikelID;
END $$

-- AFTER DELETE: відкочуємо внесок видаленого рядка закупівлі
CREATE TRIGGER trg_einkaufartikel_ad
AFTER DELETE ON einkaufartikel
FOR EACH ROW
BEGIN
  DECLARE v_cur_qty INT;
  DECLARE v_cur_avg DECIMAL(10,4);
  DECLARE v_new_qty INT;
  DECLARE v_new_total DECIMAL(18,6);
  DECLARE v_new_avg DECIMAL(10,4);

  SELECT COALESCE(lagerbestand,0), COALESCE(durchschnittskosten,0)
    INTO v_cur_qty, v_cur_avg
  FROM artikel
  WHERE artikelID = OLD.artikelID;

  SET v_new_qty   = v_cur_qty - OLD.einkaufsmenge;
  SET v_new_total = (v_cur_qty * v_cur_avg) - (OLD.einkaufsmenge * OLD.einkaufspreis);

  SET v_new_avg = CASE
                    WHEN v_new_qty > 0 THEN ROUND(v_new_total / v_new_qty, 4)
                    ELSE NULL
                  END;

  UPDATE artikel
     SET lagerbestand = v_new_qty,
         durchschnittskosten = v_new_avg
   WHERE artikelID = OLD.artikelID;
END $$


--   ПРОДАЖІ (verkaufartikel)
  
-- BEFORE INSERT: перевіряємо запас і одразу списуємо (щоб уникнути гонок)
CREATE TRIGGER trg_verkaufartikel_bi
BEFORE INSERT ON verkaufartikel
FOR EACH ROW
BEGIN
  DECLARE v_stock INT;

  SELECT COALESCE(lagerbestand,0) INTO v_stock
  FROM artikel
  WHERE artikelID = NEW.artikelID
  FOR UPDATE;

  IF NEW.verkaufsmenge IS NULL OR NEW.verkaufsmenge <= 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'verkaufsmenge must be > 0';
  END IF;

  IF v_stock < NEW.verkaufsmenge THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Not enough stock for this sale';
  END IF;

  UPDATE artikel
     SET lagerbestand = v_stock - NEW.verkaufsmenge
   WHERE artikelID = NEW.artikelID;
END $$

-- AFTER UPDATE: якщо змінилася кількість — доcписуємо/повертаємо різницю
CREATE TRIGGER trg_verkaufartikel_au
AFTER UPDATE ON verkaufartikel
FOR EACH ROW
BEGIN
  DECLARE v_cur_stock INT;
  DECLARE v_delta INT;

  SET v_delta = NEW.verkaufsmenge - OLD.verkaufsmenge; -- >0 треба додатково списати; <0 повернути

  IF v_delta <> 0 THEN
    SELECT COALESCE(lagerbestand,0) INTO v_cur_stock
    FROM artikel
    WHERE artikelID = NEW.artikelID
    FOR UPDATE;

    IF v_delta > 0 AND v_cur_stock < v_delta THEN
      SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Not enough stock to increase sales quantity';
    END IF;

    UPDATE artikel
       SET lagerbestand = v_cur_stock - v_delta
     WHERE artikelID = NEW.artikelID;
  END IF;
END $$

-- AFTER DELETE: при видаленні позиції продажу повертаємо товар на склад
CREATE TRIGGER trg_verkaufartikel_ad
AFTER DELETE ON verkaufartikel
FOR EACH ROW
BEGIN
  UPDATE artikel
     SET lagerbestand = lagerbestand + OLD.verkaufsmenge
   WHERE artikelID = OLD.artikelID;
END $$

DELIMITER ;