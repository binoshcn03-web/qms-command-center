"""
Fact_CRM_Contact generator — ONE file only.
Creates Fact_CRM_Contact.csv in Data_Source.
Grain: one row = one customer contact.
Target: 100,000+ rows.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Fact_CRM_Contact.csv"

VOICE_RANGE = (60, 72)
CHAT_RANGE = (115, 130)
EMAIL_RANGE = (26, 34)
SOCIAL_RANGE = (12, 18)
WEEKEND_FACTOR = 0.42


def to_bool_series(s):
    return s.astype(str).str.strip().str.lower().isin(["true", "1", "yes"])


def load_dims():
    date_path = SAVE_FOLDER / "Dim_Date.csv"
    emp_path = SAVE_FOLDER / "Dim_Employee.csv"
    tcd_path = SAVE_FOLDER / "Dim_TCD.csv"
    missing = [str(p) for p in (date_path, emp_path, tcd_path) if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing files:\n" + "\n".join(missing))

    dates = pd.read_csv(date_path, parse_dates=["FullDate"])
    emp = pd.read_csv(emp_path, parse_dates=["HireDate"])
    tcd = pd.read_csv(tcd_path)

    if "IsWorkingDay" in dates.columns:
        dates["IsWorkingDay"] = to_bool_series(dates["IsWorkingDay"])
    else:
        dates["IsWorkingDay"] = dates["FullDate"].dt.weekday < 5

    if "IsInScope" in tcd.columns:
        tcd["IsInScope"] = to_bool_series(tcd["IsInScope"])
    if "HierarchyDepth" in tcd.columns:
        tcd["HierarchyDepth"] = pd.to_numeric(tcd["HierarchyDepth"], errors="coerce")

    agents = emp.loc[emp["Role"].astype(str) == "Agent"].copy().reset_index(drop=True)
    leaves = tcd.loc[(tcd["IsInScope"]) & (tcd["HierarchyDepth"] == 4)].copy()
    if leaves.empty:
        leaves = tcd.loc[tcd["HierarchyDepth"] == 4].copy()
    if agents.empty or leaves.empty or dates.empty:
        raise ValueError("Dim_Date, agents, or TCD leaves are empty")
    return dates, agents, leaves


def daily_volume(rng, is_working, is_spike, channel):
    low, high = {
        "Voice": VOICE_RANGE,
        "Chat": CHAT_RANGE,
        "Email": EMAIL_RANGE,
        "Social": SOCIAL_RANGE,
    }[channel]
    n = int(rng.integers(low, high + 1))
    if not is_working:
        n = max(1, int(round(n * WEEKEND_FACTOR)))
    if is_spike:
        n = int(round(n * rng.uniform(1.35, 1.65)))
    return n


def is_spike_date(ts):
    key = (int(ts.month), int(ts.day))
    prime = key in {(7, 15), (7, 16), (7, 17), (10, 13), (10, 14)}
    festival = (ts.month == 10 and 18 <= ts.day <= 24) or (ts.month == 11 and 1 <= ts.day <= 8)
    year_end = ts.month == 12 and ts.day >= 20
    return prime or festival or year_end


def pick_handle_sec(rng, channel, n):
    if channel == "Voice":
        return np.clip(rng.lognormal(6.05, 0.42, n), 90, 2400).astype(int)
    if channel == "Chat":
        return np.clip(rng.lognormal(6.55, 0.40, n), 180, 3600).astype(int)
    if channel == "Email":
        return np.clip(rng.lognormal(6.90, 0.35, n), 300, 5400).astype(int)
    return np.clip(rng.lognormal(6.40, 0.38, n), 120, 2400).astype(int)


def build():
    rng = np.random.default_rng(SEED)
    dates, agents, leaves = load_dims()

    if "MixWeightHint" in leaves.columns:
        tcd_weight = pd.to_numeric(leaves["MixWeightHint"], errors="coerce").fillna(1).to_numpy(dtype=float)
    else:
        tcd_weight = np.ones(len(leaves), dtype=float)
    if tcd_weight.sum() <= 0:
        tcd_weight = np.ones(len(leaves), dtype=float)
    tcd_weight = tcd_weight / tcd_weight.sum()

    agent_ids = agents["EmployeeID"].astype(str).to_numpy()
    agent_hire = pd.to_datetime(agents["HireDate"])
    agent_site = agents["Site"].astype(str).to_numpy()
    agent_ldap = agents["LDAP"].astype(str).to_numpy()
    agent_channel = agents["PrimaryChannel"].astype(str).to_numpy()
    agent_shift = agents["Shift"].astype(str).to_numpy()
    agent_sup = agents["SupervisorID"].astype(str).to_numpy()
    agent_qa = agents["QualityAnalystID"].astype(str).to_numpy()

    frames = []
    seq = 1

    for rec in dates.itertuples(index=False):
        day = pd.Timestamp(rec.FullDate).normalize()
        working = bool(rec.IsWorkingDay)
        spike = is_spike_date(day)

        for channel in ("Voice", "Chat", "Email", "Social"):
            n = daily_volume(rng, working, spike, channel)

            match = np.where(agent_channel == channel)[0]
            if len(match) >= 8:
                pool = match
            else:
                pool = np.arange(len(agents))
            a_idx = rng.choice(pool, size=n, replace=True)

            t_idx = rng.choice(len(leaves), size=n, p=tcd_weight)
            tcd_block = leaves.iloc[t_idx]

            if channel == "Voice":
                hour = rng.choice(
                    np.arange(7, 23),
                    size=n,
                    p=np.array([2, 3, 5, 7, 8, 8, 7, 7, 8, 8, 7, 6, 5, 4, 3, 2], dtype=float) / 90,
                )
            elif channel == "Chat":
                hour = rng.choice(
                    np.arange(7, 24),
                    size=n,
                    p=np.array([2, 3, 4, 6, 7, 8, 7, 7, 8, 8, 7, 6, 5, 4, 4, 3, 2], dtype=float) / 91,
                )
            else:
                hour = rng.choice(np.arange(8, 22), size=n)

            minute = rng.integers(0, 60, size=n)
            second = rng.integers(0, 60, size=n)
            start_dt = day + pd.to_timedelta(hour, unit="h") + pd.to_timedelta(minute, unit="m") + pd.to_timedelta(second, unit="s")

            handle = pick_handle_sec(rng, channel, n)
            queue = np.clip(rng.lognormal(3.4, 0.7, n), 5, 900).astype(int)
            if channel == "Voice":
                hold = np.where(rng.random(n) < 0.38, np.clip(rng.lognormal(2.8, 0.9, n), 0, 600).astype(int), 0)
            else:
                hold = np.zeros(n, dtype=int)
            wrap = np.clip(rng.lognormal(3.6, 0.5, n), 15, 420).astype(int)
            if channel == "Voice":
                talk = np.clip(handle - hold, 30, None).astype(int)
            else:
                talk = np.zeros(n, dtype=int)

            if channel == "Chat":
                first_resp = np.clip(rng.lognormal(3.2, 0.6, n), 8, 240).astype(int)
                chat_msgs = rng.integers(6, 45, size=n)
            elif channel == "Social":
                first_resp = np.clip(rng.lognormal(4.2, 0.5, n), 30, 1800).astype(int)
                chat_msgs = np.zeros(n, dtype=int)
            else:
                first_resp = np.zeros(n, dtype=int)
                chat_msgs = np.zeros(n, dtype=int)

            hire_for_rows = agent_hire.iloc[a_idx]
            tenure_days = (day - hire_for_rows).dt.days.to_numpy()
            tenure_days = np.clip(tenure_days, 0, None).astype(int)
            new_hire = tenure_days <= 90

            resolved = rng.random(n) < np.where(new_hire, 0.78, 0.88)
            transferred = rng.random(n) < 0.11
            abandoned = (channel == "Voice") & (rng.random(n) < 0.04)
            resolved = np.where(abandoned, False, resolved)
            escalated = (~resolved) & (rng.random(n) < 0.35)

            csat_offered = (~abandoned) & (rng.random(n) < 0.42)
            raw_csat = rng.choice([1, 2, 3, 4, 5], size=n, p=[0.05, 0.07, 0.13, 0.35, 0.40])
            raw_csat = np.where(new_hire & (rng.random(n) < 0.20), np.minimum(raw_csat, 3), raw_csat)
            raw_csat = np.where((~resolved) & (rng.random(n) < 0.45), np.minimum(raw_csat, 2), raw_csat)
            csat = np.where(csat_offered, raw_csat, np.nan)

            repeat7 = (~resolved) | (rng.random(n) < 0.08)
            repeat30 = repeat7 | (rng.random(n) < 0.07)

            prime = rng.random(n) < 0.46
            has_order = rng.random(n) < 0.82
            order_id = []
            asin = []
            for flag in has_order:
                if flag:
                    order_id.append("403-" + str(int(rng.integers(1000000, 9999999))) + "-" + str(int(rng.integers(1000000, 9999999))))
                    asin.append("B0" + str(int(rng.integers(10000000, 99999999))))
                else:
                    order_id.append("")
                    asin.append("")

            if channel == "Voice":
                transcript = rng.random(n) < 0.70
                recording = np.ones(n, dtype=bool)
                init = rng.choice(["IVR", "Direct DID", "Callback"], size=n, p=[0.78, 0.14, 0.08])
                queue_name = "AMZ_IN_Voice_Retail"
                callback = rng.random(n) < 0.06
            else:
                transcript = np.ones(n, dtype=bool)
                recording = np.zeros(n, dtype=bool)
                init = np.array([channel] * n)
                callback = np.zeros(n, dtype=bool)
                if channel == "Chat":
                    queue_name = "AMZ_IN_Chat_Retail"
                elif channel == "Email":
                    queue_name = "AMZ_IN_Email_Retail"
                else:
                    queue_name = "AMZ_IN_Social_Retail"

            keys = np.arange(seq, seq + n)
            seq += n
            marketplace = rng.choice(["IN", "IN", "IN", "AE", "SG", "US"], size=n)
            language = []
            for m in marketplace:
                if m == "IN":
                    language.append("HI" if rng.random() < 0.28 else "EN")
                else:
                    language.append("EN")

            customer_key = ["CUST-" + str(int(rng.integers(10000000, 99999999))) for _ in range(n)]
            contact_ids = ["CNT-" + str(k).zfill(8) for k in keys]
            interaction_ids = ["INT-" + str(k).zfill(8) for k in keys]
            case_ids = ["CASE-" + str(k).zfill(8) for k in keys]

            disposition = np.where(
                abandoned,
                "Abandoned",
                np.where(escalated, "Escalated", np.where(resolved, "Resolved", "Pending / Follow-up")),
            )
            disconnect = np.where(
                abandoned,
                "Customer abandon",
                rng.choice(["Agent hangup", "Customer hangup", "System"], size=n, p=[0.55, 0.38, 0.07]),
            )

            frames.append(
                pd.DataFrame(
                    {
                        "ContactID": contact_ids,
                        "InteractionID": interaction_ids,
                        "CaseID": case_ids,
                        "ContactDatetime": start_dt,
                        "ContactDate": day,
                        "DateKey": int(day.strftime("%Y%m%d")),
                        "ContactHour": hour,
                        "Channel": channel,
                        "Direction": "Inbound",
                        "QueueName": queue_name,
                        "InitiationMethod": init,
                        "EmployeeID": agent_ids[a_idx],
                        "LDAP": agent_ldap[a_idx],
                        "SupervisorID": agent_sup[a_idx],
                        "QualityAnalystID": agent_qa[a_idx],
                        "Site": agent_site[a_idx],
                        "Shift": agent_shift[a_idx],
                        "AgentTenureDaysAtContact": tenure_days,
                        "IsNewHireContact": new_hire,
                        "CustomerKey": customer_key,
                        "Marketplace": marketplace,
                        "Language": language,
                        "IsPrimeCustomer": prime,
                        "OrderID": order_id,
                        "ASIN": asin,
                        "TcdLeafKey": tcd_block["TcdLeafKey"].to_numpy(),
                        "TcdL1Code": tcd_block["TcdL1Code"].to_numpy(),
                        "Level1Product": tcd_block["Level1Product"].to_numpy(),
                        "Level2SubCategory": tcd_block["Level2SubCategory"].to_numpy(),
                        "Level3ContactReason": tcd_block["Level3ContactReason"].to_numpy(),
                        "Level4ReasonDetail": tcd_block["Level4ReasonDetail"].to_numpy(),
                        "QueueTimeSec": queue,
                        "TalkTimeSec": talk,
                        "HoldTimeSec": hold,
                        "WrapTimeSec": wrap,
                        "HandleTimeSec": handle,
                        "FirstResponseTimeSec": first_resp,
                        "ChatMessageCount": chat_msgs,
                        "IsAbandoned": abandoned,
                        "IsTransferred": transferred,
                        "IsEscalated": escalated,
                        "IsResolved": resolved,
                        "IsRepeatContact7d": repeat7,
                        "IsRepeatContact30d": repeat30,
                        "CallbackRequested": callback,
                        "Disposition": disposition,
                        "DisconnectType": disconnect,
                        "RecordingAvailable": recording,
                        "TranscriptAvailable": transcript,
                        "SurveyOffered": csat_offered,
                        "CsatScore": csat,
                        "IsDsat": np.where(csat_offered, csat <= 2, False),
                        "AfterHoursFlag": (hour < 8) | (hour >= 21),
                        "VolumeSpikeDay": spike,
                    }
                )
            )

    fact = pd.concat(frames, ignore_index=True)
    fact["DateKey"] = pd.to_datetime(fact["ContactDate"]).dt.strftime("%Y%m%d").astype(int)
    return fact.sort_values("ContactDatetime").reset_index(drop=True)


def main():
    SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
    fact = build()
    if len(fact) < 100000:
        raise ValueError("Row count " + str(len(fact)) + " is below 100000")
    fact.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print("SUCCESS")
    print("File created:")
    print(OUTPUT_FILE)
    print("Rows:", len(fact))
    print("From:", pd.to_datetime(fact["ContactDate"]).min().date(), "To:", pd.to_datetime(fact["ContactDate"]).max().date())
    print(fact["Channel"].value_counts().to_string())
    print("Resolve rate:", round(float(fact["IsResolved"].mean()), 3))


if __name__ == "__main__":
    main()