"""
Fact_Sampling_Plan — ONE file.
Grain: one row = Site x Channel x month target.
Target = 5 audits per tenured FTE per month, split across channels.
Attainment target 95% (BEST QM).
"""

from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Fact_Sampling_Plan.csv"
CHANNELS = ["Voice", "Chat", "Email", "Social"]
CHANNEL_SHARE = {"Voice": 0.34, "Chat": 0.48, "Email": 0.12, "Social": 0.06}


def main():
    date_path = SAVE_FOLDER / "Dim_Date.csv"
    emp_path = SAVE_FOLDER / "Dim_Employee.csv"
    missing = [str(p) for p in (date_path, emp_path) if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing files:\n" + "\n".join(missing))

    dates = pd.read_csv(date_path, parse_dates=["FullDate"])
    emp = pd.read_csv(emp_path)
    agents = emp.loc[emp["Role"].astype(str) == "Agent"]
    months = sorted(pd.to_datetime(dates["FullDate"]).dt.to_period("M").unique())
    rng = np.random.default_rng(SEED)

    rows = []
    plan_id = 1
    for month in months:
        start = month.to_timestamp()
        end = (month.to_timestamp() + pd.offsets.MonthEnd(0))
        for site, site_n in agents.groupby("Site").size().items():
            for channel in CHANNELS:
                base = int(round(site_n * 5 * CHANNEL_SHARE[channel]))
                target = max(4, int(round(base * rng.uniform(0.92, 1.08))))
                rows.append(
                    {
                        "SamplingPlanID": "SP-" + str(plan_id).zfill(5),
                        "YearMonth": str(month),
                        "PeriodStart": start.date(),
                        "PeriodEnd": end.date(),
                        "Site": site,
                        "Channel": channel,
                        "SamplingTechnique": "Stratified",
                        "TargetAuditCount": target,
                        "AttainmentTargetPct": 0.95,
                        "PlanOwnerRole": "Quality Lead",
                    }
                )
                plan_id += 1

    out = pd.DataFrame(rows)
    SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False)
    print("SUCCESS")
    print(OUTPUT_FILE)
    print("Rows:", len(out))


if __name__ == "__main__":
    main()