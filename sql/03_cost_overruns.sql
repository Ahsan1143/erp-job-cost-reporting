-- 03_cost_overruns.sql
-- Cost codes forecast to finish over budget, worst first.
SELECT
    r.job_no,
    j.job_name,
    r.cost_code,
    r.description,
    r.cost_type,
    ROUND(r.revised_budget, 0)                              AS revised_budget,
    ROUND(r.forecast_at_completion, 0)                      AS forecast_cost,
    ROUND(r.forecast_at_completion - r.revised_budget, 0)   AS forecast_overrun,
    ROUND(100.0 * (r.forecast_at_completion - r.revised_budget) / r.revised_budget, 1)
                                                            AS overrun_pct,
    ROUND(r.cpi, 3)                                         AS cpi
FROM v_cost_code_report r
JOIN jobs j ON j.job_no = r.job_no
WHERE r.forecast_at_completion - r.revised_budget > 25000
ORDER BY forecast_overrun DESC;
