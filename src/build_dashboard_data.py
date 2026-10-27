"""Build the JSON that feeds dashboard/index.html from the SQL reporting layer.

Usage:  python src/build_dashboard_data.py
"""
from pathlib import Path
import json
import pandas as pd
import build_database

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql"


def main() -> None:
    con = build_database.build()
    wip = pd.read_sql((SQL / "02_wip_schedule.sql").read_text(), con)
    labour = pd.read_sql((SQL / "05_labour_productivity.sql").read_text(), con)
    wip = wip.merge(labour[["job_no", "productivity_factor"]], on="job_no", how="left")
    codes = pd.read_sql("""
        SELECT job_no, cost_code, description, cost_type, revised_budget, actual_cost,
               committed, pct_complete, cpi, forecast_at_completion
        FROM v_cost_code_report""", con)
    monthly = pd.read_sql((SQL / "04_monthly_cost_trend.sql").read_text(), con)
    bills = pd.read_sql("SELECT job_no, fiscal_period, SUM(gross_billed) AS billed FROM billings GROUP BY 1, 2", con)

    def r(x, n=2):
        return None if pd.isna(x) else round(float(x), n)

    data = {
        "company": "Boreal Ridge Construction Ltd. (fictional)",
        "reportDate": "2026-09-30",
        "jobs": [{
            "job": j.job_no, "name": j.job_name, "pm": j.project_manager, "status": j.status,
            "contract": r(j.revised_contract, 0), "budget": r(j.revised_budget, 0), "cost": r(j.cost_to_date, 0),
            "forecast": r(j.forecast_cost, 0), "pct": r(j.pct_complete, 4), "earned": r(j.earned_revenue, 0),
            "billed": r(j.billed_to_date, 0), "overUnder": r(j.over_under_billing, 0),
            "gp": r(j.projected_gross_profit, 0), "margin": r(j.projected_margin_pct, 4),
            "bidMargin": r(j.bid_margin_pct, 4), "cpi": r(j.cpi, 3), "backlog": r(j.backlog, 0),
            "productivity": r(j.productivity_factor, 3),
        } for j in wip.itertuples()],
        "codes": [{
            "job": c.job_no, "code": c.cost_code, "desc": c.description, "type": c.cost_type,
            "budget": r(c.revised_budget, 0), "actual": r(c.actual_cost, 0), "forecast": r(c.forecast_at_completion, 0),
            "cpi": r(c.cpi, 3), "pct": r(c.pct_complete, 3),
        } for c in codes.itertuples()],
        "monthly": [{"job": m.job_no, "p": int(m.fiscal_period), "cost": r(m.monthly_cost, 0)} for m in monthly.itertuples()],
        "billing": [{"job": b.job_no, "p": int(b.fiscal_period), "billed": r(b.billed, 0)} for b in bills.itertuples()],
    }
    out = ROOT / "dashboard" / "dashboard_data.json"
    out.write_text(json.dumps(data, separators=(",", ":")))
    # inline the data into the dashboard page so it works as a single file
    page = ROOT / "dashboard" / "index.html"
    tpl = (ROOT / "dashboard" / "template.html").read_text()
    page.write_text(tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":"))))
    print(f"Wrote {out.name} and {page.name}: {len(data['jobs'])} jobs, {len(data['codes'])} cost lines")


if __name__ == "__main__":
    main()
