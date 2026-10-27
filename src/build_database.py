"""Load the ERP export CSVs into SQLite and create the reporting view.

Usage:  python src/build_database.py
"""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "job_cost.db"
TABLES = ["jobs", "cost_codes", "budgets", "progress", "commitments", "job_cost_detail", "billings"]


def build() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    for t in TABLES:
        pd.read_csv(DATA / f"{t}.csv").to_sql(t, con, if_exists="replace", index=False)
    con.executescript((ROOT / "sql" / "01_cost_code_report.sql").read_text())
    return con


if __name__ == "__main__":
    con = build()
    wip = pd.read_sql((ROOT / "sql" / "02_wip_schedule.sql").read_text(), con)
    print(wip.to_string(index=False))
