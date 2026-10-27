-- 04_monthly_cost_trend.sql
-- Monthly and cumulative cost by job (window function running total).
SELECT
    job_no,
    fiscal_period,
    ROUND(SUM(amount), 2)                                                       AS monthly_cost,
    ROUND(SUM(SUM(amount)) OVER (PARTITION BY job_no ORDER BY fiscal_period), 2) AS cumulative_cost
FROM job_cost_detail
GROUP BY job_no, fiscal_period
ORDER BY job_no, fiscal_period;
