"""
Fact_Calibration — ONE file.
Grain: one row = Gauge score vs Evaluator score on the same audit.
Tolerance: 10%.
"""

from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
TOLERANCE = 0.10
SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Fact_Calibration.csv"


def to_bool(s):
    return s.astype(str).str.strip().str.lower().isin(["true", "1", "yes"])


def main():
    ev_path = SAVE_FOLDER / "Fact_QA_Evaluation.csv"
    emp_path = SAVE_FOLDER / "Dim_Employee.csv"
    missing = [str(p) for p in (ev_path, emp_path) if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing files:\n" + "\n".join(missing))

    ev = pd.read_csv(ev_path, parse_dates=["EvaluatedDatetime"], low_memory=False)
    emp = pd.read_csv(emp_path)
    rng = np.random.default_rng(SEED)

    if "IsGaugeEligible" in emp.columns:
        emp["IsGaugeEligible"] = to_bool(emp["IsGaugeEligible"])
        gauges = emp.loc[emp["IsGaugeEligible"]].copy()
    else:
        gauges = emp.loc[emp["Role"].astype(str).isin(["Quality Manager", "Trainer"])].copy()
    if gauges.empty:
        raise ValueError("No Gauge employees found")

    n = min(max(int(len(ev) * 0.04), 400), len(ev))
    pick = rng.choice(len(ev), size=n, replace=False)
    base = ev.iloc[pick].reset_index(drop=True)

    g_ids = gauges["EmployeeID"].astype(str).to_numpy()
    gauge_id = rng.choice(g_ids, size=n, replace=True)

    ev_score = pd.to_numeric(base["ClientQualityScore"], errors="coerce").fillna(0).to_numpy()
    if "IsFatalAudit" in base.columns:
        fatal = to_bool(base["IsFatalAudit"]).to_numpy()
    else:
        fatal = np.zeros(n, dtype=bool)

    inside = rng.random(n) >= 0.12
    inner = rng.uniform(-TOLERANCE + 0.005, TOLERANCE - 0.005, n)
    outer = rng.choice([-1.0, 1.0], size=n) * rng.uniform(TOLERANCE + 0.02, 0.26, n)
    var = np.where(inside, inner, outer)
    gauge_score = np.clip(ev_score * (1 + var), 0, 100)
    gauge_score = np.where(fatal & (rng.random(n) < 0.80), 0.0, gauge_score)
    ev_score = np.where(fatal, 0.0, ev_score)

    with np.errstate(divide="ignore", invalid="ignore"):
        variance = np.where(gauge_score == 0, np.where(ev_score == 0, 0.0, 1.0), (ev_score - gauge_score) / gauge_score)
    variance = np.nan_to_num(variance, nan=0.0)

    session_dt = pd.to_datetime(base["EvaluatedDatetime"]) + pd.to_timedelta(rng.integers(4, 96, size=n), unit="h")
    keys = np.arange(1, n + 1)
    out = pd.DataFrame(
        {
            "CalibrationID": ["CAL-" + str(k).zfill(8) for k in keys],
            "EvaluationID": base["EvaluationID"].astype(str).to_numpy(),
            "ContactID": base["ContactID"].astype(str).to_numpy() if "ContactID" in base.columns else [""] * n,
            "EvaluatorEmployeeID": base["EvaluatorEmployeeID"].astype(str).to_numpy() if "EvaluatorEmployeeID" in base.columns else [""] * n,
            "GaugeEmployeeID": gauge_id,
            "CalibrationDatetime": session_dt,
            "DateKey": session_dt.dt.strftime("%Y%m%d").astype(int),
            "FormVersion": base["FormVersion"].astype(str).to_numpy() if "FormVersion" in base.columns else ["AMZ-EOF-v1.0"] * n,
            "EvaluatorScore": np.round(ev_score, 2),
            "GaugeScore": np.round(gauge_score, 2),
            "VariancePct": np.round(variance, 4),
            "AbsVariancePct": np.round(np.abs(variance), 4),
            "TolerancePct": TOLERANCE,
            "IsOutsideTolerance": np.abs(variance) > TOLERANCE,
            "Site": base["Site"].astype(str).to_numpy() if "Site" in base.columns else [""] * n,
            "Channel": base["Channel"].astype(str).to_numpy() if "Channel" in base.columns else [""] * n,
        }
    )
    SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print("SUCCESS")
    print(OUTPUT_FILE)
    print("Rows:", len(out))
    print("Outside tolerance:", round(float(out["IsOutsideTolerance"].mean()), 3))


if __name__ == "__main__":
    main()