USE newshopdb;

-- 1) Закриваємо поточні прайси до 2025-09-30
UPDATE artikelpreis
SET gueltig_ab = '2024-01-01'
WHERE gueltig_ab = '2024-12-31';

-- 2) Вставляємо нові прайси з 2025-10-01 = попередня_ціна * 1.05
INSERT INTO artikelpreis (artikelID, listenpreis, gueltig_ab, gueltig_bis)
SELECT
    t.artikelID,
    ROUND(t.listenpreis * 0.95, 2)       AS new_listenpreis,
    '2024-01-01'                         AS gueltig_ab,
    '2024-12-31'                         AS gueltig_bis
FROM (
    -- беремо «актуальну на 30.09» ціну по кожному артикулу
    SELECT ap1.artikelID, ap1.listenpreis
    FROM artikelpreis ap1
    JOIN (
        SELECT artikelID, MAX(gueltig_ab) AS max_ab
        FROM artikelpreis
        WHERE gueltig_ab = '2025-01-01'
        GROUP BY artikelID
    ) last ON last.artikelID = ap1.artikelID AND last.max_ab = ap1.gueltig_ab
) t;


UPDATE verkaufartikel va
JOIN verkauf v       ON v.verkaufID = va.verkaufID
JOIN artikelpreis ap ON ap.artikelID = va.artikelID
                    AND ap.gueltig_ab <= v.verkaufsdatum
                    AND (ap.gueltig_bis IS NULL OR ap.gueltig_bis >= v.verkaufsdatum)
SET va.verkaufspreis = ap.listenpreis
WHERE v.verkaufsdatum <= '2024-12-31';

select * from artikelpreis;


SELECT * FROM artikelpreis;

