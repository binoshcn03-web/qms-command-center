#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repair after append_refresh_facts.py duplicated EvaluationID on Calibration.

1) Strip rows in 1–12 Sep 2026 from facts (the first append).
2) Re-append with unique IDs.
3) New calibration/coaching rows point at NEW evaluation IDs only (one each).

Put in Python_Scripts, run:
  python repair_refresh_facts.py
Then Desktop → Refresh.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260913
rng = np.random.default_rng(SEED)

SCRIPT_DIR = Path(__file__).resolve().parent
DATA = SCRIPT_DIR.parent / "Data_Source"

NEW_START = pd.Timestamp("2026-09-01")
NEW_END = pd.Timestamp("2026-09-12")
CUT = 20260901


def read_csv(name: str) -> pd.DataFrame:
    p = DATA / name
    if not p.exists():
        raise FileNotFoundError(p)
    return pd.read_csv(p, encoding="utf-8")


def write_csv(name: str, df: pd.DataFrame) -> None:
    df.to_csv(DATA / name, index=False, encoding="utf-8")
    print(f"  {name}: {len(df):,} rows")


def pick(df: pd.DataFrame, names: list[str]) -> str | None:
    for n in names:
        if n in df.columns:
            return n
    return None


def datekey(ts: pd.Timestamp) -> int:
    return int(ts.strftime("%Y%m%d"))


def is_new_row(df: pd.DataFrame) -> pd.Series:
    key = pick(df, ["DateKey"])
    if key is not None:
        k = pd.to_numeric(df[key], errors="coerce")
        return k >= CUT
    for c in [
        "EvaluatedDatetime",
        "EvaluatedDate",
        "ContactDatetime",
        "ContactDate",
        "CoachingDatetime",
        "CalibrationDatetime",
        "PeriodStart",
        "FullDate",
    ]:
        if c in df.columns:
            d = pd.to_datetime(df[c], errors="coerce")
            return (d >= NEW_START) & (d <= NEW_END + pd.Timedelta(days=1))
    return pd.Series(False, index=df.index)


def strip_new(name: str) -> pd.DataFrame:
    df = read_csv(name)
    mask = is_new_row(df)
    n = int(mask.sum())
    keep = df.loc[~mask].copy()
    print(f"strip {name}: removed {n:,}, keep {len(keep):,}")
    return keep


def next_numeric_id(series: pd.Series, prefix: str) -> int:
    nums = pd.to_numeric(series.astype(str).str.extract(r"(\d+)$", expand=False), errors="coerce")
    if nums.notna().any():
        return int(nums.max()) + 1
    return 1


def stamp_dates(sample: pd.DataFrame, n: int) -> pd.DatetimeIndex:
    days = pd.date_range(NEW_START, NEW_END, freq="D")
    chosen = pd.to_datetime(rng.choice(days, size=n))
    sec = rng.integers(8 * 3600, 20 * 3600, size=n)
    return chosen, chosen + pd.to_timedelta(sec, unit="s")


def apply_times(sample: pd.DataFrame, chosen, stamps) -> None:
    for c in ["EvaluatedDatetime", "ContactDatetime", "FeedbackDueDatetime",
              "CoachingDatetime", "DeliveredDatetime", "CalibrationDatetime"]:
        if c in sample.columns:
            sample[c] = pd.Series(stamps).dt.strftime("%Y-%m-%d %H:%M:%S").values
    for c in ["EvaluatedDate", "ContactDate", "CoachingDate", "CalibrationDate", "PeriodStart"]:
        if c in sample.columns:
            sample[c] = pd.Series(chosen).dt.strftime("%Y-%m-%d").values
    if "DateKey" in sample.columns:
        sample["DateKey"] = [datekey(d) for d in chosen]


def assign_ids(sample: pd.DataFrame, col: str | None, prefix: str, start: int) -> None:
    if col and col in sample.columns:
        sample[col] = [f"{prefix}{start + i:08d}" for i in range(len(sample))]


def main() -> None:
    if not DATA.exists():
        raise FileNotFoundError(DATA)

    print("DATA =", DATA)

    # --- strip first-append rows ---
    qa_name = "Fact_QA_Evaluation.csv"
    crm_name = "Fact_CRM_Contact.csv"
    coa_name = "Fact_Coaching.csv"
    cal_name = "Fact_Calibration.csv"
    smp_name = "Fact_Sampling_Plan.csv"

    qa = strip_new(qa_name)
    crm = strip_new(crm_name) if (DATA / crm_name).exists() else None
    coa = strip_new(coa_name) if (DATA / coa_name).exists() else None
    cal = strip_new(cal_name) if (DATA / cal_name).exists() else None

    if (DATA / smp_name).exists():
        smp = strip_new(smp_name)
        write_csv(smp_name, smp)

    # --- re-append CRM ---
    if crm is not None:
        n = 8000
        sample = crm.sample(n=n, replace=True, random_state=SEED).reset_index(drop=True)
        chosen, stamps = stamp_dates(sample, n)
        apply_times(sample, chosen, stamps)
        idc = pick(sample, ["ContactID"])
        assign_ids(sample, idc, "CNT-", next_numeric_id(crm[idc], "CNT-") if idc else 1)
        if "InteractionID" in sample.columns and idc != "InteractionID":
            assign_ids(sample, "InteractionID", "INT-", next_numeric_id(crm["InteractionID"], "INT-"))
        crm_out = pd.concat([crm, sample[crm.columns]], ignore_index=True)
        write_csv(crm_name, crm_out)

    # --- re-append QA with brand-new EvaluationIDs ---
    n_qa = 400
    q_sample = qa.sample(n=n_qa, replace=True, random_state=SEED).reset_index(drop=True)
    chosen, stamps = stamp_dates(q_sample, n_qa)
    apply_times(q_sample, chosen, stamps)
    ev_col = pick(qa, ["EvaluationID"])
    ev_start = next_numeric_id(qa[ev_col], "EVL-") if ev_col else 1
    assign_ids(q_sample, ev_col, "EVL-", ev_start)
    if "ContactID" in q_sample.columns:
        assign_ids(q_sample, "ContactID", "CNT-", next_numeric_id(qa["ContactID"], "CNT-") if "ContactID" in qa.columns else 900000)
    new_eval_ids = q_sample[ev_col].astype(str).tolist() if ev_col else []
    qa_out = pd.concat([qa, q_sample[qa.columns]], ignore_index=True)
    write_csv(qa_name, qa_out)

    # --- calibration: ONE row per chosen NEW evaluation (unique EvaluationID) ---
    if cal is not None and new_eval_ids:
        n_cal = min(40, len(new_eval_ids))
        cal_ids = new_eval_ids[:n_cal]  # unique slice
        c_sample = cal.sample(n=n_cal, replace=True, random_state=SEED).reset_index(drop=True)
        chosen, stamps = stamp_dates(c_sample, n_cal)
        apply_times(c_sample, chosen, stamps)
        if ev_col and ev_col in c_sample.columns:
            c_sample[ev_col] = cal_ids
        cid = pick(cal, ["CalibrationID"])
        assign_ids(c_sample, cid, "CAL-", next_numeric_id(cal[cid], "CAL-") if cid else 1)
        # if a unique-eval constraint existed, ensure uniqueness
        if ev_col and ev_col in c_sample.columns:
            assert c_sample[ev_col].is_unique
            overlap = set(cal[ev_col].astype(str)) & set(c_sample[ev_col].astype(str))
            if overlap:
                raise RuntimeError(f"EvaluationID overlap on calibration: {list(overlap)[:3]}")
        cal_out = pd.concat([cal, c_sample[cal.columns]], ignore_index=True)
        write_csv(cal_name, cal_out)

    # --- coaching: unique EvaluationID from remaining new evals ---
    if coa is not None and new_eval_ids:
        used = set(new_eval_ids[:40])
        rest = [e for e in new_eval_ids if e not in used]
        n_coa = min(200, len(rest) if rest else len(new_eval_ids))
        pool = rest if rest else new_eval_ids
        # unique — do not reuse within coaching
        coa_ids = pool[:n_coa]
        n_coa = len(coa_ids)
        k_sample = coa.sample(n=n_coa, replace=True, random_state=SEED).reset_index(drop=True)
        chosen, stamps = stamp_dates(k_sample, n_coa)
        apply_times(k_sample, chosen, stamps)
        if ev_col and ev_col in k_sample.columns:
            k_sample[ev_col] = coa_ids
        kid = pick(coa, ["CoachingID", "CoachingSessionID"])
        prefix = "COA-"
        assign_ids(k_sample, kid, prefix, next_numeric_id(coa[kid], prefix) if kid else 1)
        if ev_col and ev_col in k_sample.columns:
            assert k_sample[ev_col].is_unique
        coa_out = pd.concat([coa, k_sample[coa.columns]], ignore_index=True)
        write_csv(coa_name, coa_out)

    print("DONE. Close the CSVs in Excel if open. Desktop → Refresh.")


if __name__ == "__main__":
    main()
