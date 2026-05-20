-- Year-over-year growth in platform nights, by country.
--
-- Only counts years with all 12 months observed (partial years would
-- distort the comparison). Uses LAG to compute prev-year nights inline,
-- then percentage change.

WITH yearly AS (
    SELECT
        geo,
        year,
        SUM(nights) AS annual_nights
    FROM platform_country_month
    WHERE indic_to = 'NGT_SP'
      AND c_resid  = 'TOTAL'
    GROUP BY geo, year
    HAVING COUNT(DISTINCT month) = 12
),
with_lag AS (
    SELECT
        geo,
        year,
        annual_nights,
        LAG(annual_nights) OVER (PARTITION BY geo ORDER BY year) AS prev_nights
    FROM yearly
)
SELECT
    geo,
    year,
    annual_nights,
    prev_nights,
    ROUND((annual_nights - prev_nights) * 100.0 / NULLIF(prev_nights, 0), 1)
        AS yoy_pct
FROM with_lag
WHERE prev_nights IS NOT NULL
ORDER BY geo, year;
