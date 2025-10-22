USE newshopdb;

CREATE OR REPLACE VIEW v_umschlag_90tage AS
SELECT
  -- COGS за 90 днів (за поточними durchschnittskosten):
  (SELECT SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0))
     FROM verkauf v
     JOIN verkaufartikel va ON va.verkaufID = v.verkaufID
     JOIN artikel a         ON a.artikelID   = va.artikelID
    WHERE v.verkaufsdatum >= NOW() - INTERVAL 90 DAY)                           AS cogs_90,
  -- Поточна вартість запасів:
  (SELECT SUM(a2.lagerbestand * COALESCE(a2.durchschnittskosten,0))
     FROM artikel a2)                                                           AS lagerwert_now,
  -- Оборотність (разів за 90 днів):
  ROUND(
    (SELECT SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0))
       FROM verkauf v
       JOIN verkaufartikel va ON va.verkaufID = v.verkaufID
       JOIN artikel a         ON a.artikelID   = va.artikelID
      WHERE v.verkaufsdatum >= NOW() - INTERVAL 90 DAY)
    /
    NULLIF((SELECT SUM(a2.lagerbestand * COALESCE(a2.durchschnittskosten,0))
              FROM artikel a2), 0), 2)                                          AS umschlag_90_approx,
  -- Середня тривалість зберігання (днів):
  ROUND(
    CASE
      WHEN (SELECT SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0))
              FROM verkauf v
              JOIN verkaufartikel va ON va.verkaufID = v.verkaufID
              JOIN artikel a         ON a.artikelID   = va.artikelID
             WHERE v.verkaufsdatum >= NOW() - INTERVAL 90 DAY) = 0
      THEN NULL
      ELSE 90 /
        (
          (SELECT SUM(va.verkaufsmenge * COALESCE(a.durchschnittskosten,0))
             FROM verkauf v
             JOIN verkaufartikel va ON va.verkaufID = v.verkaufID
             JOIN artikel a         ON a.artikelID   = va.artikelID
            WHERE v.verkaufsdatum >= NOW() - INTERVAL 90 DAY)
          /
          NULLIF((SELECT SUM(a2.lagerbestand * COALESCE(a2.durchschnittskosten,0))
                    FROM artikel a2), 0)
        )
    END, 1)                                                                    AS lagerdauer_tage;

SELECT * FROM v_umschlag_90tage;
