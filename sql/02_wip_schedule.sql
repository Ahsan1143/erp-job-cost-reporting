-- =============================================================================
-- 02_wip_schedule.sql
-- Work-in-progress (WIP) schedule by job: percentage-of-completion revenue
-- (cost-to-cost method), projected margin and over/under billing.
-- =============================================================================
WITH cost AS (
    SELECT job_no,
           SUM(revised_budget)          AS revised_budget,
           SUM(actual_cost)             AS cost_to_date,
           SUM(committed)               AS committed,
           SUM(earned_value)            AS earned_value,
           SUM(forecast_at_completion)  AS forecast_cost
    FROM v_cost_code_report
    GROUP BY job_no
),
billed AS (
    SELECT job_no, SUM(gross_billed) AS billed_to_date, SUM(holdback_retained) AS holdback
    FROM billings
    GROUP BY job_no
)
SELECT
    j.job_no,
    j.job_name,
    j.project_manager,
    j.status,
    j.revised_contract,
    ROUND(c.revised_budget, 2)                                           AS revised_budget,
    ROUND(c.cost_to_date, 2)                                             AS cost_to_date,
    ROUND(c.forecast_cost, 2)                                            AS forecast_cost,
    ROUND(c.forecast_cost - c.cost_to_date, 2)                           AS cost_to_complete,
    ROUND(c.cost_to_date / c.forecast_cost, 4)                           AS pct_complete,
    ROUND(j.revised_contract * c.cost_to_date / c.forecast_cost, 2)      AS earned_revenue,
    ROUND(b.billed_to_date, 2)                                           AS billed_to_date,
    ROUND(b.billed_to_date
          - j.revised_contract * c.cost_to_date / c.forecast_cost, 2)    AS over_under_billing,
    ROUND(j.revised_contract - c.forecast_cost, 2)                       AS projected_gross_profit,
    ROUND((j.revised_contract - c.forecast_cost) / j.revised_contract, 4) AS projected_margin_pct,
    j.bid_margin_pct,
    ROUND((j.revised_contract - c.forecast_cost) / j.revised_contract
          - j.bid_margin_pct, 4)                                         AS margin_fade_pct_pts,
    ROUND(c.earned_value / c.cost_to_date, 3)                            AS cpi,
    ROUND(j.revised_contract
          - j.revised_contract * c.cost_to_date / c.forecast_cost, 2)    AS backlog
FROM jobs j
JOIN cost c   ON c.job_no = j.job_no
LEFT JOIN billed b ON b.job_no = j.job_no
ORDER BY j.job_no;
