"""
Fact_Coaching — ONE file.
Grain: one row = one coaching / feedback session.
Only failed audits from Fact_QA_Evaluation.
"""

from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Fact_Coaching.csv"


def to_bool(s):
    return s.astype(str).str.strip().str.lower().isin(["true", "1", "yes"])


def pick_action(is_fatal, is_nh, failed_list):
    text = str(failed_list)
    if is_fatal or "QP01" in text or "QP02" in text or "QP03" in text or "QP04" in text:
        if "QP01" in text or "QP02" in text:
            return "ACT-15"
        return "ACT-03"
    if is_nh:
        return "ACT-05"
    if "QP08" in text or "QP09" in text:
        return "ACT-04"
    if "QP15" in text:
        return "ACT-08"
    if "QP13" in text:
        return "ACT-12"
    if "QP14" in text:
        return "ACT-13"
    if "QP16" in text:
        return "ACT-14"
    if "QP11" in text:
        return "ACT-11"
    return "ACT-01"


def main():
    ev_path = SAVE_FOLDER / "Fact_QA_Evaluation.csv"
    emp_path = SAVE_FOLDER / "Dim_Employee.csv"
    act_path = SAVE_FOLDER / "Dim_Coaching.csv"
    missing = [str(p) for p in (ev_path, emp_path, act_path) if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing files:\n" + "\n".join(missing))

    ev = pd.read_csv(ev_path, parse_dates=["EvaluatedDatetime"], low_memory=False)
    emp = pd.read_csv(emp_path)
    act = pd.read_csv(act_path)

    if "IsFailedAudit" in ev.columns:
        ev["IsFailedAudit"] = to_bool(ev["IsFailedAudit"])
    elif "ErrorCommitted" in ev.columns:
        ev["IsFailedAudit"] = to_bool(ev["ErrorCommitted"])
    else:
        raise ValueError("Fact_QA_Evaluation has no IsFailedAudit / ErrorCommitted")

    if "IsFatalAudit" in ev.columns:
        ev["IsFatalAudit"] = to_bool(ev["IsFatalAudit"])
    else:
        ev["IsFatalAudit"] = False
    if "IsNewHireAudit" in ev.columns:
        ev["IsNewHireAudit"] = to_bool(ev["IsNewHireAudit"])
    else:
        ev["IsNewHireAudit"] = False

    failed = ev.loc[ev["IsFailedAudit"]].copy().reset_index(drop=True)
    if failed.empty:
        raise ValueError("No failed audits to coach")

    rng = np.random.default_rng(SEED)
    n = len(failed)

    mgr = emp.set_index(emp["EmployeeID"].astype(str))["SupervisorID"].astype(str).to_dict() if "SupervisorID" in emp.columns else {}
    coach = failed["EmployeeID"].astype(str).map(mgr)
    if "SupervisorID" in failed.columns:
        coach = coach.fillna(failed["SupervisorID"].astype(str))

    actions = []
    for i in range(n):
        actions.append(
            pick_action(
                bool(failed["IsFatalAudit"].iloc[i]),
                bool(failed["IsNewHireAudit"].iloc[i]),
                failed["FailedParameterList"].iloc[i] if "FailedParameterList" in failed.columns else "",
            )
        )

    if "FeedbackDueDatetime" in failed.columns:
        due = pd.to_datetime(failed["FeedbackDueDatetime"], errors="coerce")
    else:
        due = pd.to_datetime(failed["EvaluatedDatetime"]) + pd.to_timedelta(48, unit="h")

    inside = rng.random(n) < 0.81
    delay = np.where(inside, rng.integers(2, 47, size=n), rng.integers(49, 120, size=n))
    delivered = pd.to_datetime(failed["EvaluatedDatetime"]) + pd.to_timedelta(delay, unit="h")

    keys = np.arange(1, n + 1)
    out = pd.DataFrame(
        {
            "CoachingID": ["COA-" + str(k).zfill(8) for k in keys],
            "EvaluationID": failed["EvaluationID"].astype(str).to_numpy(),
            "ContactID": failed["ContactID"].astype(str).to_numpy() if "ContactID" in failed.columns else [""] * n,
            "EmployeeID": failed["EmployeeID"].astype(str).to_numpy(),
            "CoachEmployeeID": coach.astype(str).to_numpy(),
            "CoachingActionID": actions,
            "PrimaryFailedParameters": failed["FailedParameterList"].astype(str).to_numpy() if "FailedParameterList" in failed.columns else [""] * n,
            "CoachingDatetime": delivered,
            "DateKey": delivered.dt.strftime("%Y%m%d").astype(int),
            "FeedbackDueDatetime": due.dt.strftime("%Y-%m-%d %H:%M:%S"),
            "SlaHoursTarget": 48,
            "FeedbackLagHours": delay,
            "IsSlaMet": delay <= 48,
            "CoachingChannel": rng.choice(["Floor", "Teams", "Nest desk", "Email recap"], size=n, p=[0.48, 0.32, 0.12, 0.08]),
            "AcknowledgementFlag": rng.random(n) < 0.91,
            "IsFatalRelated": failed["IsFatalAudit"].to_numpy(),
            "IsNewHireRelated": failed["IsNewHireAudit"].to_numpy(),
            "Site": failed["Site"].astype(str).to_numpy() if "Site" in failed.columns else [""] * n,
        }
    )
    out = out.merge(
        act[["CoachingActionID", "ActionName", "ActionFamily"]],
        on="CoachingActionID",
        how="left",
    )
    SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print("SUCCESS")
    print(OUTPUT_FILE)
    print("Rows:", len(out))
    print("SLA met:", round(float(out["IsSlaMet"].mean()), 3))


if __name__ == "__main__":
    main()