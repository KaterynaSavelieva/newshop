USE newshopdb;

-- Продажі за 90 днів, агреговані по артикулу (один рядок на artikelID)
-- (у MariaDB без CTE: робимо як звичайний підзапит у FROM)
CREATE OR REPLACE VIEW v_umschlag_90tage AS
SELECT
    a.artikelID,
    a.produktname,
    a.lagerbestand,
    ROUND(COALESCE(a.durchschnittskosten,0), 2)                          AS durchschnittskosten,

    -- Поточна вартість залишку по артикулу
    ROUND(a.lagerbestand * COALESCE(a.durchschnittskosten,0), 2)          AS lagerwert_now,

    -- Продана к-сть за 90 днів (штуки)
    COALESCE(s.qty_90, 0)                                                 AS verkaufsmenge_90,

    -- COGS за 90 днів (оцінюємо через поточні durchschnittskosten)
    ROUND(COALESCE(s.qty_90,0) * COALESCE(a.durchschnittskosten,0), 2)    AS cogs_90,

    -- Мін/макс історичних закуп. цін (за потреби можна прибрати)
    ROUND(COALESCE(al.min_einkaufspreis, 0), 2)                            AS min_einkaufspreis,
    ROUND(COALESCE(al.max_einkaufspreis, 0), 2)                            AS max_einkaufspreis,

    -- Оборотність = COGS_90 / Lagerwert_now
    ROUND(
      (COALESCE(s.qty_90,0) * COALESCE(a.durchschnittskosten,0))
      / NULLIF(a.lagerbestand * COALESCE(a.durchschnittskosten,0), 0)
    , 2)                                                                   AS umschlag_90_approx,

    -- Середня тривалість зберігання (днів) = 90 / оборотність
    ROUND(
      CASE
        WHEN COALESCE(s.qty_90,0) = 0
          OR a.lagerbestand * COALESCE(a.durchschnittskosten,0) = 0
        THEN NULL
        ELSE 90 /
          (
            (COALESCE(s.qty_90,0) * COALESCE(a.durchschnittskosten,0))
            / (a.lagerbestand * COALESCE(a.durchschnittskosten,0))
          )
      END
    , 1)                                                                   AS lagerdauer_tage

FROM artikel a

-- підзапит із продажами за 90 днів (один рядок на artikelID)
LEFT JOIN (
    SELECT
        va.artikelID,
        SUM(va.verkaufsmenge) AS qty_90
    FROM verkauf v
    JOIN verkaufartikel va ON va.verkaufID = v.verkaufID
    WHERE v.verkaufsdatum >= NOW() - INTERVAL 90 DAY
    GROUP BY va.artikelID
) s ON s.artikelID = a.artikelID

-- опціонально: мін/макс ціни закупівель по артикулу (окремо, щоб не множити рядки)
LEFT JOIN (
    SELECT
        ea.artikelID,
        MIN(ea.einkaufspreis) AS min_einkaufspreis,
        MAX(ea.einkaufspreis) AS max_einkaufspreis
    FROM einkaufartikel ea
    GROUP BY ea.artikelID
) al ON al.artikelID = a.artikelID;


SELECT * FROM v_umschlag_90tage;