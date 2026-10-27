"""Generate a SYNTHETIC generic-ERP job cost export for a FICTIONAL contractor.

The original version of this project was built on confidential client data.
This script creates a realistic stand-in so the reporting and dashboards can be
shared publicly. Every company, job, client and vendor here is invented.

Outputs (data/), shaped like a standard ERP job cost / AP / payroll export:
    jobs.csv               job master (contract values, dates, bid margin)
    cost_codes.csv         cost code master (phase, cost type)
    budgets.csv            original budget + approved budget changes by job / cost code
    progress.csv           PM-reported physical % complete by job / cost code
    commitments.csv        subcontracts and purchase orders
    job_cost_detail.csv    posted job cost transactions (AP, payroll, equipment, GL)
    billings.csv           monthly progress billings with 10% holdback

Run:  python src/generate_sample_data.py      (seeded, so output is reproducible)
"""
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 2026
REPORT_DATE = pd.Timestamp("2026-09-30")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
rng = np.random.default_rng(SEED)

COMPANY = "Boreal Ridge Construction Ltd. (fictional)"

# --------------------------------------------------------------------------
# Cost code master: code, description, cost type, phase window (fraction of
# the job timeline in which the work happens)
# --------------------------------------------------------------------------
COST_CODES = [
    ("01-100", "General Conditions - Supervision", "Labour",      0.00, 1.00),
    ("01-200", "Site Facilities & Temp Services",  "Other",       0.00, 1.00),
    ("01-500", "Equipment Rental",                 "Equipment",   0.02, 0.85),
    ("02-200", "Earthwork & Excavation",           "Subcontract", 0.00, 0.25),
    ("03-100", "Concrete Formwork",                "Labour",      0.08, 0.45),
    ("03-200", "Reinforcing Steel",                "Material",    0.08, 0.42),
    ("03-300", "Cast-in-Place Concrete",           "Material",    0.10, 0.48),
    ("04-200", "Masonry",                          "Subcontract", 0.35, 0.65),
    ("05-100", "Structural Steel",                 "Subcontract", 0.25, 0.55),
    ("06-100", "Rough Carpentry",                  "Labour",      0.40, 0.80),
    ("07-200", "Roofing & Insulation",             "Subcontract", 0.45, 0.70),
    ("08-100", "Doors, Frames & Hardware",         "Material",    0.60, 0.92),
    ("09-200", "Drywall & Finishes",               "Subcontract", 0.60, 0.95),
    ("15-000", "Mechanical",                       "Subcontract", 0.30, 0.97),
    ("16-000", "Electrical",                       "Subcontract", 0.30, 0.97),
]
cc = pd.DataFrame(COST_CODES, columns=["cost_code", "description", "cost_type", "phase_start", "phase_end"])
cc["division"] = cc["cost_code"].str[:2]

# Budget weights by job type (share of cost budget per cost code)
WEIGHTS = {
    "Industrial":    [8, 3, 4, 7, 6, 5, 9, 0, 16, 2, 6, 2, 4, 14, 14],
    "Institutional": [9, 3, 3, 4, 5, 4, 7, 7, 8, 4, 6, 4, 9, 15, 12],
    "Commercial":    [8, 3, 3, 5, 5, 4, 8, 4, 10, 4, 7, 4, 9, 14, 12],
    "Residential":   [8, 3, 3, 4, 4, 3, 6, 6, 4, 10, 6, 5, 12, 14, 12],
}

# --------------------------------------------------------------------------
# Job master. cpi_base < 1 means the job is running over budget.
# problem_codes get an extra cost overrun.
# --------------------------------------------------------------------------
JOBS = [
    # job_no, name, type, client_type, PM, contract, CO, bid_margin, start, finish, cpi_base, problem codes, billing_bias
    ("23-098", "Transit Bus Garage Upgrade",         "Institutional", "Municipal",          "R. Singh",    14_850_000,   612_000, 0.105, "2024-06-03", "2026-08-28", 0.985, ["15-000"],           1.00),
    ("24-101", "Leduc Distribution Warehouse",       "Industrial",    "Private developer",  "M. Okafor",   21_400_000,   845_000, 0.095, "2025-03-03", "2026-12-18", 1.010, [],                   1.06),
    ("24-104", "School Modernization - Phase 2",     "Institutional", "School board",       "J. Tremblay", 16_200_000,   338_000, 0.110, "2025-05-05", "2027-01-29", 0.950, ["03-100", "09-200"], 0.96),
    ("24-107", "Fabrication Shop Expansion",         "Industrial",    "Private industrial", "M. Okafor",    9_750_000,   410_000, 0.120, "2025-06-02", "2026-10-30", 1.030, [],                   1.03),
    ("25-110", "Medical Office Building",            "Commercial",    "Private developer",  "S. Chen",     24_600_000,   980_000, 0.100, "2025-08-04", "2027-05-28", 0.970, ["05-100"],           1.08),
    ("25-112", "Fire Hall No. 4",                    "Institutional", "Municipal",          "R. Singh",     8_900_000,   126_000, 0.115, "2025-09-08", "2026-11-27", 1.000, ["16-000"],           0.97),
    ("25-115", "Recreation Centre Retrofit",         "Institutional", "Municipal",          "J. Tremblay", 11_300_000,   765_000, 0.105, "2025-10-06", "2027-03-26", 0.930, ["15-000", "06-100"], 0.92),
    ("25-118", "Cold Storage Facility",              "Industrial",    "Private industrial", "S. Chen",     17_800_000,   290_000, 0.098, "2025-11-03", "2027-02-26", 1.020, [],                   1.05),
    ("25-121", "Seniors Residence",                  "Residential",   "Non-profit",         "A. Dubois",   19_950_000,   455_000, 0.090, "2026-01-12", "2027-08-27", 0.990, ["09-200"],           1.02),
    ("26-124", "Process Building",                   "Industrial",    "Private industrial", "M. Okafor",   13_400_000,         0, 0.115, "2026-03-02", "2027-06-25", 1.000, ["01-500"],           1.10),
    ("26-127", "Retail Plaza",                       "Commercial",    "Private developer",  "A. Dubois",    7_650_000,         0, 0.125, "2026-05-04", "2027-04-30", 1.010, [],                   1.04),
    ("26-130", "Public Works Yard Building",         "Institutional", "Municipal",          "R. Singh",     6_300_000,         0, 0.110, "2026-07-06", "2027-07-30", 1.000, [],                   1.00),
]
jobs = pd.DataFrame(JOBS, columns=["job_no", "job_name", "job_type", "client_type", "project_manager",
                                   "original_contract", "approved_change_orders", "bid_margin_pct",
                                   "start_date", "scheduled_finish", "cpi_base", "problem_codes", "billing_bias"])
jobs["start_date"] = pd.to_datetime(jobs["start_date"])
jobs["scheduled_finish"] = pd.to_datetime(jobs["scheduled_finish"])
jobs["revised_contract"] = jobs["original_contract"] + jobs["approved_change_orders"]
jobs["status"] = np.where(jobs["scheduled_finish"] <= REPORT_DATE, "Substantially complete", "In progress")


def s_curve(x):
    """Smooth 0-1 S-curve for cumulative progress (logistic, rescaled)."""
    x = np.clip(x, 0, 1)
    k = 6.5
    lo, hi = 1 / (1 + np.exp(k * 0.5)), 1 / (1 + np.exp(-k * 0.5))
    return (1 / (1 + np.exp(-k * (x - 0.5))) - lo) / (hi - lo)


def code_progress(time_frac, start, end):
    if time_frac <= start:
        return 0.0
    return float(s_curve((time_frac - start) / (end - start)))


budget_rows, progress_rows, commit_rows, txn_rows, bill_rows = [], [], [], [], []
LABOUR_RATE = {"01-100": 92.0, "03-100": 74.0, "06-100": 71.0}   # burdened $/hr
vendor_seq = iter(range(1001, 9999))
txn_id = iter(range(500001, 999999))

for _, j in jobs.iterrows():
    cost_budget = j.original_contract * (1 - j.bid_margin_pct)
    w = np.array(WEIGHTS[j.job_type], dtype=float)
    w = w * rng.uniform(0.85, 1.15, len(w))
    w = w / w.sum()
    orig_budget = np.round(cost_budget * w, -2)
    # Approved change orders carry a ~15% markup; the cost side goes to 3-4 codes
    co_cost = j.approved_change_orders * 0.85
    chg = np.zeros(len(cc))
    if co_cost > 0:
        idx = rng.choice(np.where(orig_budget > 0)[0], size=3, replace=False)
        split = rng.dirichlet(np.ones(3))
        chg[idx] = np.round(co_cost * split, -2)

    total_days = (j.scheduled_finish - j.start_date).days
    time_frac = min(max((REPORT_DATE - j.start_date).days / total_days, 0), 1)
    # monthly time grid from start to report date
    months = pd.date_range(j.start_date.to_period("M").to_timestamp(), REPORT_DATE, freq="MS")

    for k, c in cc.iterrows():
        ob, bc = orig_budget[k], chg[k]
        if ob <= 0:
            continue
        rb = ob + bc
        bh = round(rb / LABOUR_RATE[c.cost_code], 0) if c.cost_code in LABOUR_RATE else 0.0
        budget_rows.append((j.job_no, c.cost_code, ob, bc, rb, bh))
        pct = code_progress(time_frac, c.phase_start, c.phase_end)
        if j.status == "Substantially complete":
            pct = 1.0 if c.cost_code != "01-100" else 0.99
        pct = round(min(pct * rng.uniform(0.96, 1.03), 1.0), 3) if 0 < pct < 1 else round(pct, 3)
        progress_rows.append((j.job_no, c.cost_code, pct))
        if pct == 0:
            # Sub/material packages are often bought out before work starts
            if c.cost_type in ("Subcontract", "Material") and time_frac > c.phase_start - 0.25:
                commit_rows.append((j.job_no, c.cost_code, c.cost_type, round(rb * rng.uniform(0.97, 1.04), -2)))
            continue

        cpi = j.cpi_base * rng.normal(1.0, 0.025)
        if c.cost_code in j.problem_codes:
            cpi *= rng.uniform(0.80, 0.88)
        if c.cost_type in ("Subcontract", "Material"):
            # Buyout result sets the committed value; cost tracks the commitment
            committed = round(rb * rng.uniform(0.96, 1.03) / (cpi if c.cost_code in j.problem_codes else 1.0), -2)
            commit_rows.append((j.job_no, c.cost_code, c.cost_type, committed))
            actual_total = committed * pct * rng.uniform(0.97, 1.0)
        else:
            actual_total = rb * pct / cpi

        # spread the cost-to-date over months following the progress curve
        cum = []
        for m in months:
            mid = m + pd.offsets.MonthEnd(0)
            tf = min(max((mid - j.start_date).days / total_days, 0), 1)
            cum.append(code_progress(min(tf, time_frac), c.phase_start, c.phase_end))
        cum = np.array(cum)
        if cum[-1] <= 0:
            cum[-1] = 1.0
        inc = np.diff(np.concatenate([[0], cum / cum[-1]]))
        inc = np.clip(inc * rng.uniform(0.85, 1.15, len(inc)), 0, None)
        if inc.sum() == 0:
            inc[-1] = 1
        inc = inc / inc.sum()
        monthly = np.round(actual_total * inc, 2)
        monthly[-1] += round(actual_total - monthly.sum(), 2)

        vendor = None
        if c.cost_type == "Subcontract":
            vendor = (f"V{next(vendor_seq)}", f"{c.description.split(' & ')[0].split(' - ')[0]} Subcontractor {rng.choice(list('ABCDEFG'))}")
        elif c.cost_type == "Material":
            vendor = (f"V{next(vendor_seq)}", f"{c.description.split(',')[0].split(' & ')[0]} Supplier {rng.choice(list('ABCDEFG'))}")

        for m, amt in zip(months, monthly):
            if amt <= 0:
                continue
            period = int(m.strftime("%Y%m"))
            if c.cost_type == "Labour":
                rate = LABOUR_RATE[c.cost_code]
                weeks = pd.date_range(m, m + pd.offsets.MonthEnd(0), freq="W-FRI")
                parts = rng.dirichlet(np.ones(len(weeks)) * 4) * amt
                parts = np.round(parts, 2); parts[-1] += round(amt - parts.sum(), 2)
                for wk, a in zip(weeks, parts):
                    txn_rows.append((next(txn_id), wk.date(), period, j.job_no, c.cost_code, "Labour", "PR",
                                     "", "Payroll", f"Payroll w/e {wk:%b %d}", round(a / rate, 1), a))
            elif c.cost_type == "Equipment":
                txn_rows.append((next(txn_id), (m + pd.offsets.MonthEnd(0)).date(), period, j.job_no, c.cost_code,
                                 "Equipment", "EQ", "", "Internal equipment", "Monthly equipment charge", 0.0, amt))
            elif c.cost_type == "Subcontract":
                txn_rows.append((next(txn_id), (m + pd.Timedelta(days=24)).date(), period, j.job_no, c.cost_code,
                                 "Subcontract", "AP", vendor[0], vendor[1], f"Progress claim {m:%b %Y}", 0.0, amt))
            else:  # Material / Other: one to three invoices a month
                n = int(rng.integers(1, 4))
                parts = np.round(rng.dirichlet(np.ones(n) * 3) * amt, 2); parts[-1] += round(amt - parts.sum(), 2)
                for i, a in enumerate(parts):
                    d = m + pd.Timedelta(days=int(rng.integers(2, 27)))
                    vid, vname = vendor if vendor else ("V0999", "Site Services Vendor")
                    txn_rows.append((next(txn_id), d.date(), period, j.job_no, c.cost_code, c.cost_type, "AP",
                                     vid, vname, f"Invoice {rng.integers(10000, 99999)}", 0.0, a))

budgets = pd.DataFrame(budget_rows, columns=["job_no", "cost_code", "original_budget", "approved_budget_changes", "revised_budget", "budget_hours"])
progress = pd.DataFrame(progress_rows, columns=["job_no", "cost_code", "pct_complete"])
commitments = pd.DataFrame(commit_rows, columns=["job_no", "cost_code", "commitment_type", "committed_amount"])
commitments.insert(0, "commitment_no", [f"{'SC' if t == 'Subcontract' else 'PO'}-{i:05d}"
                                        for i, t in enumerate(commitments["commitment_type"], start=20001)])
txns = pd.DataFrame(txn_rows, columns=["transaction_id", "posting_date", "fiscal_period", "job_no", "cost_code",
                                       "cost_type", "source", "vendor_id", "vendor_name", "description", "hours", "amount"])
txns = txns.sort_values(["posting_date", "transaction_id"]).reset_index(drop=True)

# --------------------------------------------------------------------------
# Progress billings: earned revenue (cost-to-cost) x a billing bias, 10% holdback
# --------------------------------------------------------------------------
for _, j in jobs.iterrows():
    jb = budgets[budgets.job_no == j.job_no]
    jt = txns[txns.job_no == j.job_no]
    jc = commitments[commitments.job_no == j.job_no]
    jp = progress[progress.job_no == j.job_no]
    ac = jt["amount"].sum()
    # estimate at completion consistent with the report's method (approximation for billing purposes)
    m = jb.merge(jp, on=["job_no", "cost_code"]).merge(
        jt.groupby("cost_code")["amount"].sum().rename("ac"), on="cost_code", how="left").merge(
        jc.groupby("cost_code")["committed_amount"].sum().rename("com"), on="cost_code", how="left").fillna(0)
    eac = 0
    for _, r in m.iterrows():
        if r.com > 0:
            eac += max(r.com, r.ac)
        elif r.pct_complete > 0:
            eac += r.ac / r.pct_complete
        else:
            eac += r.revised_budget
    final_pct = ac / eac if eac else 0
    by_month = jt.groupby("fiscal_period")["amount"].sum().cumsum()
    prev = 0.0
    for period, cum_cost in by_month.items():
        earned = j.revised_contract * (cum_cost / eac)
        target = min(earned * j.billing_bias, j.revised_contract)
        gross = round(max(target - prev, 0) * rng.uniform(0.97, 1.03), 2)
        if gross <= 0:
            continue
        prev += gross
        inv_date = pd.Timestamp(year=period // 100, month=period % 100, day=1) + pd.offsets.MonthEnd(0)
        bill_rows.append((f"INV-{j.job_no}-{period}", inv_date.date(), period, j.job_no,
                          gross, round(gross * 0.10, 2), round(gross * 0.90, 2)))
billings = pd.DataFrame(bill_rows, columns=["invoice_no", "invoice_date", "fiscal_period", "job_no",
                                            "gross_billed", "holdback_retained", "net_receivable"])

# --------------------------------------------------------------------------
# Write the export files
# --------------------------------------------------------------------------
OUT.mkdir(exist_ok=True)
jobs_out = jobs.drop(columns=["cpi_base", "problem_codes", "billing_bias"]).copy()
jobs_out["start_date"] = jobs_out["start_date"].dt.date
jobs_out["scheduled_finish"] = jobs_out["scheduled_finish"].dt.date
jobs_out["company"] = COMPANY
jobs_out.to_csv(OUT / "jobs.csv", index=False)
cc[["cost_code", "description", "division", "cost_type"]].to_csv(OUT / "cost_codes.csv", index=False)
budgets.to_csv(OUT / "budgets.csv", index=False)
progress.to_csv(OUT / "progress.csv", index=False)
commitments.to_csv(OUT / "commitments.csv", index=False)
txns.to_csv(OUT / "job_cost_detail.csv", index=False)
billings.to_csv(OUT / "billings.csv", index=False)

print(f"{COMPANY} - report date {REPORT_DATE.date()}")
for name, df in [("jobs", jobs_out), ("cost codes", cc), ("budget lines", budgets), ("commitments", commitments),
                 ("job cost transactions", txns), ("billings", billings)]:
    print(f"  {name:<22} {len(df):>6,}")
print(f"  cost to date ${txns.amount.sum():,.0f} | billed ${billings.gross_billed.sum():,.0f}")
