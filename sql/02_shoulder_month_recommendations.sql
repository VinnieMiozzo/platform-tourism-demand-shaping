-- Recommended (country, month) pairs for shoulder-season campaigns.
--
-- Logic:
--   1. Pick countries with above-median demand AND peak-concentrated
--      seasonality (peak_share > 0.40). Those have meaningful size and
--      visible room to spread demand.
--   2. For each, compute each month's average demand relative to that
--      country's peak month.
--   3. Return shoulder months (Apr, May, Sep, Oct) where the demand is
--      below half of peak — meaningful gap to close.

WITH country_pick AS (
    SELECT geo
    FROM seasonality_components
    WHERE mean_annual_nights > (
        SELECT QUANTILE_CONT(mean_annual_nights, 0.5)
        FROM seasonality_components
    )
      AND peak_share > 0.40
),
country_monthly AS (
    SELECT
        m.geo,
        m.month,
        AVG(m.nights) AS avg_nights
    FROM platform_country_month m
    JOIN country_pick c USING (geo)
    WHERE m.indic_to = 'NGT_SP'
      AND m.c_resid = 'TOTAL'
    GROUP BY m.geo, m.month
),
with_peak AS (
    SELECT
        geo,
        month,
        avg_nights,
        MAX(avg_nights) OVER (PARTITION BY geo) AS peak_demand,
        avg_nights / NULLIF(MAX(avg_nights) OVER (PARTITION BY geo), 0)
            AS share_of_peak
    FROM country_monthly
)
SELECT
    geo,
    month,
    ROUND(avg_nights   / 1e3, 0) AS avg_k_nights,
    ROUND(peak_demand  / 1e3, 0) AS peak_k_nights,
    ROUND(share_of_peak, 3)      AS share_of_peak
FROM with_peak
WHERE month IN (4, 5, 9, 10)
  AND share_of_peak < 0.50
ORDER BY geo, month;
