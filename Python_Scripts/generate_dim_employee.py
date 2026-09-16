"""
Dim_Employee generator — ONE file only.
Creates Dim_Employee.csv in the sibling Data_Source folder.
Grain: one row = one FTE.
"""

from pathlib import Path

import numpy as np
import pandas as pd

AS_OF_DATE = pd.Timestamp("2026-09-08")
HEADCOUNT = 300
SEED = 42

SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Dim_Employee.csv"

SITES = ["Jaipur", "Bengaluru", "Manila", "Bogota"]
SITE_COUNTRY = {
    "Jaipur": "IN",
    "Bengaluru": "IN",
    "Manila": "PH",
    "Bogota": "CO",
}
LOBS = ["Cards", "Retail Banking", "Insurance Claims", "Digital Banking"]
CHANNELS = ["Voice", "Chat", "Email", "Social"]
SHIFTS = ["AM", "PM", "WD"]

FIRST = [
    "Aarav", "Ananya", "Rohan", "Isha", "Kabir", "Meera", "Vihaan", "Diya",
    "Arjun", "Sana", "Dev", "Nisha", "Reyansh", "Pooja", "Aditya", "Kavya",
    "Ishaan", "Riya", "Kunal", "Neha", "Harsh", "Priya", "Yash", "Anika",
    "Miguel", "Sofia", "Luis", "Camila", "Andres", "Valentina", "Carlos", "Lucia",
    "Jose", "Maria", "Diego", "Isabella", "Gabriel", "Elena", "Pedro", "Ana",
    "John", "Mary", "James", "Grace", "Paul", "Angela", "Mark", "Kristine",
    "Rico", "Joy", "Paolo", "Aisha", "Farhan", "Leila", "Omar", "Noor",
    "Naveen", "Sneha", "Vikram", "Tanvi", "Rahul", "Shruti", "Amit", "Kriti",
]
LAST = [
    "Sharma", "Patel", "Singh", "Gupta", "Iyer", "Reddy", "Khan", "Nair",
    "Verma", "Joshi", "Mehta", "Chopra", "Malhotra", "Bansal", "Kapoor", "Das",
    "Santos", "Reyes", "Cruz", "Garcia", "Lopez", "Hernandez", "Ramirez",
    "Torres", "Flores", "Mendoza", "Castillo", "Villanueva", "Bautista",
    "Fernandez", "Morales", "Navarro", "Diaz", "Romero", "Gutierrez", "Ramos",
]


def unique_names(rng, n):
    seen = set()
    out = []
    guard = 0
    while len(out) < n:
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        if name not in seen:
            seen.add(name)
            out.append(name)
        guard += 1
        if guard > 20000:
            raise RuntimeError("Could not generate enough unique names")
    return out


def tenure_bucket(days):
    if days <= 30:
        return "0-30"
    if days <= 90:
        return "31-90"
    if days <= 180:
        return "91-180"
    return ">180"


def hire_dates(rng, n, earliest, latest):
    start = pd.Timestamp(earliest)
    end = pd.Timestamp(latest)
    offsets = rng.integers(0, (end - start).days + 1, size=n)
    return pd.to_datetime(start) + pd.to_timedelta(offsets, unit="D")


def ldap_from_name(full_name, used):
    base = full_name.lower().replace(" ", ".")
    ldap = base
    i = 2
    while ldap in used:
        ldap = f"{base}{i}"
        i += 1
    used.add(ldap)
    return ldap


def build_dim_employee():
    rng = np.random.default_rng(SEED)

    # 300 FTEs: agents plus the leadership / QA spine needed for PATH() and QA assignment.
    n_om = 2
    n_am = 8
    n_sup = 24
    n_qm = 3
    n_qa = 15
    n_trainer = 2
    n_agent = HEADCOUNT - (n_om + n_am + n_sup + n_qm + n_qa + n_trainer)
    if n_agent <= 0:
        raise ValueError("Role mix exceeds headcount")

    role_plan = [
        ("Operations Manager", n_om, "L7", "2021-01-01", "2024-06-30"),
        ("Assistant Manager", n_am, "L6", "2022-01-01", "2025-03-31"),
        ("Supervisor", n_sup, "L5", "2022-06-01", "2025-12-31"),
        ("Quality Manager", n_qm, "L6", "2022-01-01", "2025-03-31"),
        ("Quality Analyst", n_qa, "L4", "2023-01-01", "2026-03-31"),
        ("Trainer", n_trainer, "L4", "2023-01-01", "2025-12-31"),
        ("Agent", n_agent, "L3", "2023-06-01", "2026-08-15"),
    ]

    rows = []
    seq = 10001
    names = unique_names(rng, HEADCOUNT)
    name_i = 0
    used_ldap = set()

    for role, n, band, hire_from, hire_to in role_plan:
        dates = hire_dates(rng, n, hire_from, hire_to)
        for i in range(n):
            site = SITES[i % len(SITES)]
            full_name = names[name_i]
            name_i += 1
            ldap = ldap_from_name(full_name, used_ldap)
            first, last = full_name.split(" ", 1)
            emp_id = f"EMP-{seq}"
            seq += 1
            hire = dates[i]
            tenure_days = int((AS_OF_DATE - hire).days)
            if tenure_days < 0:
                tenure_days = 0
            rows.append(
                {
                    "EmployeeID": emp_id,
                    "EmployeeNumber": emp_id.replace("EMP-", "N"),
                    "FirstName": first,
                    "LastName": last,
                    "EmployeeName": full_name,
                    "LDAP": ldap,
                    "Email": f"{ldap}@aethercx.example",
                    "Role": role,
                    "JobBand": band,
                    "Site": site,
                    "Country": SITE_COUNTRY[site],
                    "LOB": rng.choice(LOBS) if role in {"Agent", "Supervisor", "Assistant Manager", "Quality Analyst"} else "All LOB",
                    "PrimaryChannel": rng.choice(CHANNELS) if role == "Agent" else "",
                    "Shift": rng.choice(SHIFTS) if role in {"Agent", "Supervisor", "Quality Analyst"} else "AM",
                    "HireDate": hire,
                    "TenureDays": tenure_days,
                    "TenureBucket": tenure_bucket(tenure_days),
                    "EmploymentType": "FTE",
                    "IsActive": True,
                }
            )

    df = pd.DataFrame(rows)

    om_ids = df.loc[df["Role"] == "Operations Manager", "EmployeeID"].tolist()
    am_ids = df.loc[df["Role"] == "Assistant Manager", "EmployeeID"].tolist()
    sup_ids = df.loc[df["Role"] == "Supervisor", "EmployeeID"].tolist()
    qm_ids = df.loc[df["Role"] == "Quality Manager", "EmployeeID"].tolist()
    qa_ids = df.loc[df["Role"] == "Quality Analyst", "EmployeeID"].tolist()
    trainer_ids = df.loc[df["Role"] == "Trainer", "EmployeeID"].tolist()
    agent_ids = df.loc[df["Role"] == "Agent", "EmployeeID"].tolist()

    name_map = df.set_index("EmployeeID")["EmployeeName"].to_dict()
    site_map = df.set_index("EmployeeID")["Site"].to_dict()
    lob_map = df.set_index("EmployeeID")["LOB"].to_dict()

    manager = {}
    am_for = {}
    om_for = {}
    qa_for = {}

    for i, om in enumerate(om_ids):
        manager[om] = ""
        am_for[om] = ""
        om_for[om] = om
        qa_for[om] = ""

    for i, am in enumerate(am_ids):
        om = om_ids[i % len(om_ids)]
        manager[am] = om
        am_for[am] = am
        om_for[am] = om
        qa_for[am] = ""
        df.loc[df["EmployeeID"] == am, "Site"] = site_map[om]
        df.loc[df["EmployeeID"] == am, "Country"] = SITE_COUNTRY[site_map[om]]

    for i, sup in enumerate(sup_ids):
        am = am_ids[i % len(am_ids)]
        manager[sup] = am
        am_for[sup] = am
        om_for[sup] = om_for[am]
        qa_for[sup] = qa_ids[i % len(qa_ids)]
        df.loc[df["EmployeeID"] == sup, "Site"] = df.loc[df["EmployeeID"] == am, "Site"].iloc[0]
        df.loc[df["EmployeeID"] == sup, "Country"] = df.loc[df["EmployeeID"] == am, "Country"].iloc[0]
        df.loc[df["EmployeeID"] == sup, "LOB"] = df.loc[df["EmployeeID"] == am, "LOB"].iloc[0]

    for i, qm in enumerate(qm_ids):
        om = om_ids[i % len(om_ids)]
        manager[qm] = om
        am_for[qm] = ""
        om_for[qm] = om
        qa_for[qm] = ""

    for i, qa in enumerate(qa_ids):
        qm = qm_ids[i % len(qm_ids)]
        manager[qa] = qm
        am_for[qa] = ""
        om_for[qa] = om_for[qm]
        qa_for[qa] = qa
        df.loc[df["EmployeeID"] == qa, "Site"] = df.loc[df["EmployeeID"] == qm, "Site"].iloc[0]
        df.loc[df["EmployeeID"] == qa, "Country"] = df.loc[df["EmployeeID"] == qm, "Country"].iloc[0]

    for i, tr in enumerate(trainer_ids):
        qm = qm_ids[i % len(qm_ids)]
        manager[tr] = qm
        am_for[tr] = ""
        om_for[tr] = om_for[qm]
        qa_for[tr] = ""

    for i, ag in enumerate(agent_ids):
        sup = sup_ids[i % len(sup_ids)]
        manager[ag] = sup
        am_for[ag] = am_for[sup]
        om_for[ag] = om_for[sup]
        qa_for[ag] = qa_for[sup]
        df.loc[df["EmployeeID"] == ag, "Site"] = df.loc[df["EmployeeID"] == sup, "Site"].iloc[0]
        df.loc[df["EmployeeID"] == ag, "Country"] = df.loc[df["EmployeeID"] == sup, "Country"].iloc[0]
        df.loc[df["EmployeeID"] == ag, "LOB"] = df.loc[df["EmployeeID"] == sup, "LOB"].iloc[0]

    df["SupervisorID"] = df["EmployeeID"].map(lambda x: manager.get(x, "") if df.loc[df["EmployeeID"] == x, "Role"].iloc[0] == "Agent" else (manager.get(x, "") if df.loc[df["EmployeeID"] == x, "Role"].iloc[0] == "Supervisor" else ""))
    # Cleaner explicit columns from the maps
    df["SupervisorID"] = [
        manager[eid] if role == "Agent" else ""
        for eid, role in zip(df["EmployeeID"], df["Role"])
    ]
    df["SupervisorName"] = df["SupervisorID"].map(lambda x: name_map.get(x, ""))
    df["AssistantManagerID"] = df["EmployeeID"].map(am_for).fillna("")
    df["AssistantManagerName"] = df["AssistantManagerID"].map(lambda x: name_map.get(x, ""))
    df["OperationsManagerID"] = df["EmployeeID"].map(om_for).fillna("")
    df["OperationsManagerName"] = df["OperationsManagerID"].map(lambda x: name_map.get(x, ""))
    df["QualityAnalystID"] = df["EmployeeID"].map(qa_for).fillna("")
    df["QualityAnalystName"] = df["QualityAnalystID"].map(lambda x: name_map.get(x, ""))
    df["ManagerEmployeeID"] = df["EmployeeID"].map(manager).fillna("")
    df["ManagerName"] = df["ManagerEmployeeID"].map(lambda x: name_map.get(x, ""))

    df["TeamName"] = np.where(
        df["SupervisorName"] != "",
        "Team " + df["SupervisorName"].str.split().str[0],
        np.where(df["Role"] == "Supervisor", "Team " + df["EmployeeName"].str.split().str[0], ""),
    )
    df["NestingDaysTarget"] = np.where(df["Role"] == "Agent", 90, 0)
    df["NestingEndDate"] = np.where(
        df["Role"] == "Agent",
        df["HireDate"] + pd.to_timedelta(90, unit="D"),
        pd.NaT,
    )
    df["NestingEndDate"] = pd.to_datetime(df["NestingEndDate"], errors="coerce")
    df["IsNewHire"] = (df["Role"] == "Agent") & (df["TenureDays"] <= 90)
    df["IsPeopleManager"] = df["Role"].isin(
        ["Supervisor", "Assistant Manager", "Operations Manager", "Quality Manager"]
    )
    df["IsEvaluator"] = df["Role"].isin(["Quality Analyst", "Quality Manager", "Trainer"])
    df["IsGaugeEligible"] = df["Role"].isin(["Quality Manager", "Trainer"])
    df["AsOfDate"] = AS_OF_DATE

    ordered = [
        "EmployeeID",
        "EmployeeNumber",
        "EmployeeName",
        "FirstName",
        "LastName",
        "LDAP",
        "Email",
        "Role",
        "JobBand",
        "Site",
        "Country",
        "LOB",
        "PrimaryChannel",
        "Shift",
        "TeamName",
        "HireDate",
        "TenureDays",
        "TenureBucket",
        "IsNewHire",
        "NestingDaysTarget",
        "NestingEndDate",
        "SupervisorID",
        "SupervisorName",
        "AssistantManagerID",
        "AssistantManagerName",
        "OperationsManagerID",
        "OperationsManagerName",
        "QualityAnalystID",
        "QualityAnalystName",
        "ManagerEmployeeID",
        "ManagerName",
        "EmploymentType",
        "IsActive",
        "IsPeopleManager",
        "IsEvaluator",
        "IsGaugeEligible",
        "AsOfDate",
    ]
    return df[ordered].sort_values("EmployeeID").reset_index(drop=True)


def main():
    SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
    dim = build_dim_employee()
    if len(dim) != HEADCOUNT:
        raise ValueError(f"Expected {HEADCOUNT} rows, got {len(dim)}")
    if dim["EmployeeID"].duplicated().any():
        raise ValueError("Duplicate EmployeeID")
    if dim["LDAP"].duplicated().any():
        raise ValueError("Duplicate LDAP")
    dim.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d")
    print("SUCCESS")
    print("File created:")
    print(OUTPUT_FILE)
    print("Rows:", len(dim))
    print(dim["Role"].value_counts().to_string())
    print("Tenure buckets:")
    print(dim["TenureBucket"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()