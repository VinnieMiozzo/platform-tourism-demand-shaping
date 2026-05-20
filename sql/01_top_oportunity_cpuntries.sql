-- Top countries by composite shoulder-season opportunity score.
--
-- Combines three signals: demand level, growth, and peak concentration
-- (peak-heavy demand = more shoulder room available). Each component is
-- percentile-ranked so the scales are comparable, then weighted.
--
-- Mirrors the pandas scoring in notebooks/02_analysis.py with the
-- default weights (0.4 / 0.3 / 0.3).

WITH ranked AS (
    SELECT
        geo,
        mean_annual_nights,
        yoy_growth_pct,
        peak_share,
        shoulder_share,
        off_share,
        PERCENT_RANK() OVER (ORDER BY mean_annual_nights) AS level_rank,
        PERCENT_RANK() OVER (ORDER BY yoy_growth_pct)     AS growth_rank,
        PERCENT_RANK() OVER (ORDER BY peak_share)         AS peak_rank
    FROM seasonality_components
    WHERE yoy_growth_pct IS NOT NULL
)
SELECT
    geo,
    ROUND(mean_annual_nights / 1e6, 2) AS mean_annual_m_nights,
    ROUND(yoy_growth_pct, 1)           AS yoy_growth_pct,
    ROUND(peak_share, 3)               AS peak_share,
    ROUND(shoulder_share, 3)           AS shoulder_share,
    ROUND(
        0.4 * level_rank + 0.3 * growth_rank + 0.3 * peak_rank,
        3
    ) AS opportunity_score
FROM ranked
ORDER BY opportunity_score DESC
LIMIT 15;
