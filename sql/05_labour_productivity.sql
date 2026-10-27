-- 05_labour_productivity.sql
-- Self-performed labour: earned hours vs. actual hours (productivity factor
-- above 1.0 means crews are ahead of the budgeted hours for the work done).
SELECT
    job_no,
    ROUND(SUM(budget_hours), 0)                          AS budget_hours,
    ROUND(SUM(earned_hours), 0)                          AS earned_hours,
    ROUND(SUM(actual_hours), 0)                          AS actual_hours,
    ROUND(SUM(earned_hours) / NULLIF(SUM(actual_hours), 0), 3) AS productivity_factor
FROM v_cost_code_report
WHERE cost_type = 'Labour'
GROUP BY job_no
ORDER BY job_no;
