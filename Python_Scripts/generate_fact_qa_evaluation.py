"""
Fact_QA_Evaluation generator — ONE file only.
Creates Fact_QA_Evaluation.csv in Data_Source.

Grain: one row = one audit of one CRM contact.
NOT 100% of CRM. Stratified sample:
  - New hire 0-30 days: 100%
  - New hire 31-90 days: 40%
  - CompC-sensitive TCD: 50%
  - DSAT or escalated: 40%
  - All other contacts: 9%
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Fact_QA_Evaluation.csv"
FORM_VERSION = "AMZ-EOF-v1.0"

QP_COLS = [
    "QP01_SecurityVerification",
    "QP02_PrivacyGdpr",
    "QP03_PaymentRefundIntegrity",
    "QP04_PolicyDisclosure",
    "QP05_IssueIdentification",
    "QP06_ResolutionSop",
    "QP07_FcrAttempt",
    "QP08_CourtesyEmpathy",
    "QP09_OwnershipControl",
    "QP10_CorrectInformation",
    "QP11_EscalationAccuracy",
    "QP12_ExpectationNextSteps",
    "QP13_CrmDocumentation",
    "QP14_TcdAccuracy",
    "QP15_KbAdherence",
    "QP16_HoldTransferProtocol",
    "QP17_DispositionAccuracy",
    "QP18_RequiredOfferPath",
    "QP19_OpeningBranding",
    "QP20_ClosingRecap",
]

WEIGHT = {
    "QP01_SecurityVerification": 8,
    "QP02_PrivacyGdpr": 8,
    "QP03_PaymentRefundIntegrity": 8,
    "QP04_PolicyDisclosure": 7,
    "QP05_IssueIdentification": 6,
    "QP06_ResolutionSop": 8,
    "QP07_FcrAttempt": 7,
    "QP08_CourtesyEmpathy": 6,
    "QP09_OwnershipControl": 5,
    "QP10_CorrectInformation": 6,
    "QP11_EscalationAccuracy": 5,
    "QP12_ExpectationNextSteps": 5,
    "QP13_CrmDocumentation": 5,
    "QP14_TcdAccuracy": 4,
    "QP15_KbAdherence": 4,
    "QP16_HoldTransferProtocol": 3,
    "QP17_DispositionAccuracy": 3,
    "QP18_RequiredOfferPath": 2,
    "QP19_OpeningBranding": 0,
    "QP20_ClosingRecap": 0,
}

COMPC = QP_COLS[0:4]
CC = QP_COLS[4:12]
BC = QP_COLS[12:18]
RIDER = QP_COLS[18:20]
SCORING = QP_COLS[0:18]

SENSITIVE_L1 = {
    "Account and Login",
    "Payments and Amazon Pay",
    "Amazon Pharmacy",
    "Gift Cards and Gifting",
}
DISCLOSURE_L1 = {
    "Amazon Pharmacy",
    "Gift Cards and Gifting",
    "Account and Login",
    "Payments and Amazon Pay",
    "Marketplace Seller Issues",
}
OFFER_L1 = {
    "Prime Membership",
    "Returns",
    "Refunds",
    "Delivery and Tracking",
    "Marketplace Seller Issues",
    "Damaged Missing and Packaging",
}


def to_bool(s):
    return s.astype(str).str.strip().str.lower().isin(["true", "1", "yes"])


def load_source():
    crm_path = SAVE_FOLDER / "Fact_CRM_Contact.csv"
    emp_path = SAVE_FOLDER / "Dim_Employee.csv"
    missing = [str(p) for p in (crm_path, emp_path) if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing files:\n" + "\n".join(missing))

    crm = pd.read_csv(
        crm_path,
        parse_dates=["ContactDatetime", "ContactDate"],
        low_memory=False,
    )
    emp = pd.read_csv(emp_path)

    for col in ["IsDsat", "IsEscalated", "IsNewHireContact", "IsResolved", "SurveyOffered"]:
        if col in crm.columns:
            crm[col] = to_bool(crm[col])
        else:
            crm[col] = False

    if "AgentTenureDaysAtContact" in crm.columns:
        crm["AgentTenureDaysAtContact"] = pd.to_numeric(crm["AgentTenureDaysAtContact"], errors="coerce").fillna(999)
    else:
        crm["AgentTenureDaysAtContact"] = 999

    if "IsEvaluator" in emp.columns:
        emp["IsEvaluator"] = to_bool(emp["IsEvaluator"])
    evaluators = emp.loc[emp["IsEvaluator"]].copy()
    if evaluators.empty:
        evaluators = emp.loc[emp["Role"].astype(str).isin(["Quality Analyst", "Quality Manager", "Trainer"])].copy()
    if evaluators.empty:
        raise ValueError("No evaluators found in Dim_Employee")
    return crm, evaluators


def sample_mask(crm, rng):
    tenure = crm["AgentTenureDaysAtContact"].to_numpy()
    l1 = crm["Level1Product"].astype(str)
    sensitive = l1.isin(SENSITIVE_L1).to_numpy()
    dsat = crm["IsDsat"].to_numpy()
    esc = crm["IsEscalated"].to_numpy()

    rate = np.full(len(crm), 0.09, dtype=float)
    rate = np.where(sensitive, np.maximum(rate, 0.50), rate)
    rate = np.where(dsat | esc, np.maximum(rate, 0.40), rate)
    rate = np.where((tenure > 30) & (tenure <= 90), np.maximum(rate, 0.40), rate)
    rate = np.where(tenure <= 30, 1.00, rate)
    return rng.random(len(crm)) < rate


def evaluation_type(tenure, sensitive, dsat, esc, spot_flag):
    if tenure <= 90:
        return "New Hire"
    if sensitive:
        return "Fatal Review"
    if spot_flag:
        return "Spot Check"
    return "Standard"


def rate_one(rng, fail_p, na_flag):
    if na_flag:
        return "NA"
    if rng.random() < fail_p:
        return "No"
    return "Yes"


def build():
    rng = np.random.default_rng(SEED)
    crm, evaluators = load_source()
    keep = sample_mask(crm, rng)
    sample = crm.loc[keep].copy().reset_index(drop=True)
    n = len(sample)
    if n == 0:
        raise ValueError("Sampling produced 0 audits")

    ev_ids = evaluators["EmployeeID"].astype(str).to_numpy()
    assigned = sample["QualityAnalystID"].astype(str).to_numpy() if "QualityAnalystID" in sample.columns else np.array([""] * n)
    use_assigned = np.isin(assigned, ev_ids) & (rng.random(n) < 0.60)
    random_ev = rng.choice(ev_ids, size=n, replace=True)
    evaluator_id = np.where(use_assigned, assigned, random_ev)

    lag_hours = rng.integers(3, 60, size=n)
    evaluated_dt = pd.to_datetime(sample["ContactDatetime"]) + pd.to_timedelta(lag_hours, unit="h")

    tenure = sample["AgentTenureDaysAtContact"].to_numpy()
    new_hire = tenure <= 90
    l1 = sample["Level1Product"].astype(str)
    channel = sample["Channel"].astype(str)
    sensitive = l1.isin(SENSITIVE_L1).to_numpy()
    spot_flag = rng.random(n) < 0.08

    types = []
    for i in range(n):
        types.append(
            evaluation_type(
                tenure[i],
                sensitive[i],
                bool(sample["IsDsat"].iloc[i]),
                bool(sample["IsEscalated"].iloc[i]),
                bool(spot_flag[i]),
            )
        )

    qp16_na = channel.isin(["Email", "Social"]).to_numpy()
    qp04_na = (~l1.isin(DISCLOSURE_L1)).to_numpy()
    qp18_na = (~l1.isin(OFFER_L1)).to_numpy()

    fail_compc = np.where(new_hire, 0.012, 0.005)
    fail_cc = np.where(new_hire, 0.13, 0.045)
    fail_bc = np.where(new_hire, 0.15, 0.06)
    fail_rider = np.where(new_hire, 0.10, 0.05)

    ratings = {col: [] for col in QP_COLS}
    for i in range(n):
        for col in COMPC:
            na = (col == "QP04_PolicyDisclosure" and qp04_na[i])
            ratings[col].append(rate_one(rng, float(fail_compc[i]), na))
        for col in CC:
            ratings[col].append(rate_one(rng, float(fail_cc[i]), False))
        for col in BC:
            na = (col == "QP16_HoldTransferProtocol" and qp16_na[i]) or (
                col == "QP18_RequiredOfferPath" and qp18_na[i]
            )
            ratings[col].append(rate_one(rng, float(fail_bc[i]), na))
        for col in RIDER:
            ratings[col].append(rate_one(rng, float(fail_rider[i]), False))

    fact = pd.DataFrame(ratings)

    applicable = np.zeros(n, dtype=int)
    passed = np.zeros(n, dtype=int)
    score = np.zeros(n, dtype=float)
    failed_list = []
    failed_count = np.zeros(n, dtype=int)
    has_cc = np.zeros(n, dtype=bool)
    has_bc = np.zeros(n, dtype=bool)
    has_compc = np.zeros(n, dtype=bool)

    for i in range(n):
        w_yes = 0.0
        w_ans = 0.0
        misses = []
        for col in SCORING:
            val = fact.at[i, col]
            w = WEIGHT[col]
            if val == "NA":
                continue
            applicable[i] += 1
            if val == "Yes":
                passed[i] += 1
                w_yes += w
                w_ans += w
            else:
                misses.append(col[:4])
                w_ans += w
                if col in CC:
                    has_cc[i] = True
                if col in BC:
                    has_bc[i] = True
                if col in COMPC:
                    has_compc[i] = True
        for col in RIDER:
            if fact.at[i, col] == "No":
                misses.append(col[:4])
        failed_list.append("|".join(misses))
        failed_count[i] = len(misses)
        if w_ans == 0:
            score[i] = 0.0
        else:
            score[i] = round(100.0 * w_yes / w_ans, 2)

    is_fatal = has_compc
    is_failed = has_cc | has_bc | has_compc
    score = np.where(is_fatal, 0.0, score)

    due = evaluated_dt + pd.to_timedelta(48, unit="h")
    due_out = due.astype("object")
    due_out = np.where(is_failed, due.dt.strftime("%Y-%m-%d %H:%M:%S"), "")

    keys = np.arange(1, n + 1)
    out = pd.DataFrame(
        {
            "EvaluationID": ["EVL-" + str(k).zfill(8) for k in keys],
            "ContactID": sample["ContactID"].astype(str).to_numpy(),
            "InteractionID": sample["InteractionID"].astype(str).to_numpy(),
            "CaseID": sample["CaseID"].astype(str).to_numpy() if "CaseID" in sample.columns else [""] * n,
            "FormVersion": FORM_VERSION,
            "EvaluationType": types,
            "EvaluatedDatetime": evaluated_dt,
            "EvaluatedDate": evaluated_dt.dt.normalize(),
            "DateKey": evaluated_dt.dt.strftime("%Y%m%d").astype(int),
            "ContactDatetime": sample["ContactDatetime"].to_numpy(),
            "Channel": sample["Channel"].astype(str).to_numpy(),
            "QueueName": sample["QueueName"].astype(str).to_numpy() if "QueueName" in sample.columns else [""] * n,
            "Site": sample["Site"].astype(str).to_numpy() if "Site" in sample.columns else [""] * n,
            "Marketplace": sample["Marketplace"].astype(str).to_numpy() if "Marketplace" in sample.columns else [""] * n,
            "Language": sample["Language"].astype(str).to_numpy() if "Language" in sample.columns else [""] * n,
            "EmployeeID": sample["EmployeeID"].astype(str).to_numpy(),
            "LDAP": sample["LDAP"].astype(str).to_numpy() if "LDAP" in sample.columns else [""] * n,
            "SupervisorID": sample["SupervisorID"].astype(str).to_numpy() if "SupervisorID" in sample.columns else [""] * n,
            "EvaluatorEmployeeID": evaluator_id,
            "QualityAnalystID": assigned,
            "AgentTenureDaysAtContact": tenure,
            "IsNewHireAudit": new_hire,
            "TcdLeafKey": sample["TcdLeafKey"].astype(str).to_numpy() if "TcdLeafKey" in sample.columns else [""] * n,
            "Level1Product": l1.to_numpy(),
            "Level3ContactReason": sample["Level3ContactReason"].astype(str).to_numpy() if "Level3ContactReason" in sample.columns else [""] * n,
            "Disposition": sample["Disposition"].astype(str).to_numpy() if "Disposition" in sample.columns else [""] * n,
            "HandleTimeSec": sample["HandleTimeSec"].to_numpy() if "HandleTimeSec" in sample.columns else [0] * n,
            "CsatScore": sample["CsatScore"].to_numpy() if "CsatScore" in sample.columns else [np.nan] * n,
            "IsDsat": sample["IsDsat"].to_numpy(),
            "IsResolved": sample["IsResolved"].to_numpy(),
        }
    )

    for col in QP_COLS:
        out[col] = fact[col]

    out["ScoringParametersApplicable"] = applicable
    out["ScoringParametersPassed"] = passed
    out["ClientQualityScore"] = score
    out["HasCustomerCriticalError"] = has_cc
    out["HasBusinessCriticalError"] = has_bc
    out["HasComplianceCriticalError"] = has_compc
    out["IsFatalAudit"] = is_fatal
    out["IsFailedAudit"] = is_failed
    out["FailedParameterList"] = failed_list
    out["FailedParameterCount"] = failed_count
    out["ErrorCommitted"] = is_failed
    out["FeedbackRequired"] = is_failed
    out["FeedbackDueDatetime"] = due_out
    return out, len(crm)


def main():
    SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
    fact, crm_n = build()
    audit_pct = 100.0 * len(fact) / crm_n
    if audit_pct >= 95:
        raise ValueError("Audit percent is " + str(round(audit_pct, 1)) + " — sampling failed, near 100%")
    fact.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print("SUCCESS")
    print("File created:")
    print(OUTPUT_FILE)
    print("CRM rows:", crm_n)
    print("Audit rows:", len(fact))
    print("Audit percent:", round(audit_pct, 2))
    print(fact["EvaluationType"].value_counts().to_string())
    print("Fail rate:", round(float(fact["IsFailedAudit"].mean()), 3))
    print("Fatal rate:", round(float(fact["IsFatalAudit"].mean()), 3))
    print("Feedback required:", int(fact["FeedbackRequired"].sum()))
    print("Mean score:", round(float(fact["ClientQualityScore"].mean()), 2))


if __name__ == "__main__":
    main()