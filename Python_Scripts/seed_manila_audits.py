#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add CRM contacts + QA evaluations for the Manila site so Page 1
does not go blank when that site is selected.

Put in Python_Scripts:
  python seed_manila_audits.py

Then Desktop → Refresh → Publish.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260914
rng = np.random.default_rng(SEED)

SCRIPT_DIR = Path(__file__).resolve().parent
DATA = SCRIPT_DIR.parent / "Data_Source"

N_CRM = 1200
N_QA = 180
WINDOW_START = pd.Timestamp("2026-08-01")
WINDOW_END = pd.Timestamp("2026-08-31")


def read(name: str) -> pd.DataFrame:
    p = DATA / name
    if not p.exists():
        raise FileNotFoundError(p)
    return pd.read_csv(p, encoding="utf-8")


def write(name: str, df: pd.DataFrame) -> None:
    df.to_csv(DATA / name, index=False, encoding="utf-8")
    print(f"  {name}: {len(df):,} rows")


def pick(df: pd.DataFrame, names: list[str]) -> str | None:
    for n in names:
        if n in df.columns:
            return n
    return None


def datekey(ts: pd.Timestamp) -> int:
    return int(ts.strftime("%Y%m%d"))


def next_id(series: pd.Series, prefix: str) -> int:
    nums = pd.to_numeric(series.astype(str).str.extract(r"(\d+)$", expand=False), errors="coerce")
    return int(nums.max()) + 1 if nums.notna().any() else 1


def site_mask(s: pd.Series) -> pd.Series:
    t = s.astype(str).str.strip().str.lower()
    return t.str.contains("manila") | t.eq("manilla")


def apply_times(df: pd.DataFrame, n: int) -> pd.DatetimeIndex:
    days = pd.date_range(WINDOW_START, WINDOW_END, freq="D")
    chosen = pd.to_datetime(rng.choice(days, size=n))
    stamps = chosen + pd.to_timedelta(rng.integers(8 * 3600, 20 * 3600, size=n), unit="s")
    for c in ["ContactDatetime", "EvaluatedDatetime", "FeedbackDueDatetime", "ClosedDatetime"]:
        if c in df.columns:
            df[c] = pd.Series(stamps).dt.strftime("%Y-%m-%d %H:%M:%S").values
    for c in ["ContactDate", "EvaluatedDate"]:
        if c in df.columns:
            df[c] = pd.Series(chosen).dt.strftime("%Y-%m-%d").values
    if "DateKey" in df.columns:
        df["DateKey"] = [datekey(d) for d in chosen]
    return chosen


def clean_date_cols(df: pd.DataFrame) -> pd.DataFrame:
    for c in ["ContactDate", "EvaluatedDate", "FullDate", "CoachingDate", "CalibrationDate", "PeriodStart"]:
        if c in df.columns:
            dt = pd.to_datetime(df[c], errors="coerce")
            df[c] = dt.dt.strftime("%Y-%m-%d").where(dt.notna(), other="")
    return df


def main() -> None:
    emp = read("Dim_Employee.csv")
    site_c = pick(emp, ["Site"])
    emp_c = pick(emp, ["EmployeeID"])
    if site_c is None or emp_c is None:
        raise ValueError("Dim_Employee needs Site and EmployeeID")

    manila_emp = emp.loc[site_mask(emp[site_c]), emp_c].astype(str)
    site_label = emp.loc[site_mask(emp[site_c]), site_c].iloc[0]
    print(f"Site label in dim: {site_label!r}")
    print(f"Employees at site: {manila_emp.nunique()}")
    if manila_emp.empty:
        raise SystemExit("No employee whose Site contains Manila/Manilla. Check Dim_Employee[Site].")

    emp_ids = manila_emp.tolist()

    crm = read("Fact_CRM_Contact.csv")
    qa = read("Fact_QA_Evaluation.csv")

    # --- CRM ---
    c_add = crm.sample(n=N_CRM, replace=True, random_state=SEED).reset_index(drop=True)
    apply_times(c_add, N_CRM)
    if "EmployeeID" in c_add.columns:
        c_add["EmployeeID"] = rng.choice(emp_ids, size=N_CRM)
    if "Site" in c_add.columns:
        c_add["Site"] = site_label
    cid = pick(crm, ["ContactID"])
    if cid:
        start = next_id(crm[cid], "CNT-")
        c_add[cid] = [f"CNT-{start + i:08d}" for i in range(N_CRM)]
    if "InteractionID" in c_add.columns:
        start_i = next_id(crm["InteractionID"], "INT-")
        c_add["InteractionID"] = [f"INT-{start_i + i:08d}" for i in range(N_CRM)]
    crm_out = clean_date_cols(pd.concat([crm, c_add[crm.columns]], ignore_index=True))
    write("Fact_CRM_Contact.csv", crm_out)

    # --- QA (unique EvaluationID) ---
    q_add = qa.sample(n=N_QA, replace=True, random_state=SEED).reset_index(drop=True)
    apply_times(q_add, N_QA)
    if "EmployeeID" in q_add.columns:
        q_add["EmployeeID"] = rng.choice(emp_ids, size=N_QA)
    if "Site" in q_add.columns:
        q_add["Site"] = site_label
    ev = pick(qa, ["EvaluationID"])
    if ev:
        start_e = next_id(qa[ev], "EVL-")
        q_add[ev] = [f"EVL-{start_e + i:08d}" for i in range(N_QA)]
        # keep unique vs existing
        if set(q_add[ev].astype(str)) & set(qa[ev].astype(str)):
            raise RuntimeError("EvaluationID collision")
    if "ContactID" in q_add.columns:
        start_c = next_id(qa["ContactID"], "CNT-")
        q_add["ContactID"] = [f"CNT-{start_c + i:08d}" for i in range(N_QA)]
    qa_out = clean_date_cols(pd.concat([qa, q_add[qa.columns]], ignore_index=True))
    write("Fact_QA_Evaluation.csv", qa_out)

    print("DONE. Refresh. Date in Aug 2026 + Manila/Manilla should show Audits > 0.")


if __name__ == "__main__":
    main()
