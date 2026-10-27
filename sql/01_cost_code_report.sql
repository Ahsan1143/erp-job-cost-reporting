-- =============================================================================
-- 01_cost_code_report.sql
-- Job cost report at cost-code level, built from the ERP export tables.
--
-- Forecast method (estimate at completion, EAC):
--   * Subcontract / material lines with a commitment: the greater of the
--     committed value and cost to date (the commitment covers the full scope).
--   * Lines with progress but no commitment (labour, equipment, other):
--     cost to date + remaining budget / CPI  (current productivity continues).
--   * Lines not started: revised budget.
-- =============================================================================
DROP VIEW IF EXISTS v_cost_code_report;
CREATE VIEW v_cost_code_report AS
WITH actuals AS (
    SELECT job_no, cost_code,
           SUM(amount) AS actual_cost,
           SUM(hours)  AS actual_hours
    FROM job_cost_detail
    GROUP BY job_no, cost_code
),
commits AS (
    SELECT job_no, cost_code, SUM(committed_amount) AS committed
    FROM commitments
    GROUP BY job_no, cost_code
),
base AS (
    SELECT
        b.job_no,
        b.cost_code,
        c.description,
        c.cost_type,
        b.original_budget,
        b.approved_budget_changes,
        b.revised_budget,
        b.budget_hours,
        COALESCE(a.actual_cost, 0)                     AS actual_cost,
        COALESCE(a.actual_hours, 0)                    AS actual_hours,
        COALESCE(k.committed, 0)                       AS committed,
        COALESCE(p.pct_complete, 0)                    AS pct_complete,
        b.revised_budget * COALESCE(p.pct_complete, 0) AS earned_value
    FROM budgets b
    JOIN cost_codes c       ON c.cost_code = b.cost_code
    LEFT JOIN actuals a     ON a.job_no = b.job_no AND a.cost_code = b.cost_code
    LEFT JOIN commits k     ON k.job_no = b.job_no AND k.cost_code = b.cost_code
    LEFT JOIN progress p    ON p.job_no = b.job_no AND p.cost_code = b.cost_code
)
SELECT
    *,
    CASE WHEN actual_cost > 0 THEN earned_value / actual_cost END          AS cpi,
    CASE
        WHEN committed > 0       THEN MAX(committed, actual_cost)
        WHEN pct_complete > 0    THEN actual_cost + (revised_budget - earned_value)
                                      / (earned_value / actual_cost)
        ELSE revised_budget
    END                                                                     AS forecast_at_completion,
    budget_hours * pct_complete                                             AS earned_hours
FROM base;
