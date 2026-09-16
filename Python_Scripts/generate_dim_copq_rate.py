"""
Dim_COPQ_Rate — ONE file.
Grain: one row = one defect-class cost assumption.
"""

from pathlib import Path
import pandas as pd

SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Dim_COPQ_Rate.csv"

ROWS = [
    ("COP-FT", "Fatal / zero-tolerance miss", "Internal Failure", 185.00, 420.00, "CompC / fatal audit", "Regulatory review + rework + gesture"),
    ("COP-PR", "Privacy / GDPR miss", "External Failure", 260.00, 900.00, "QP02", "Incident review + notification risk"),
    ("COP-RS", "Resolution / SOP miss", "Internal Failure", 28.50, 75.00, "QP06 QP07 QP10", "Repeat contact + handle-time waste"),
    ("COP-DC", "Documentation / KB / TCD miss", "Appraisal", 9.75, 18.00, "QP13 QP14 QP15 QP17", "QA rework"),
    ("COP-SS", "Soft-skill / empathy miss", "External Failure", 16.00, 55.00, "QP08 QP09", "DSAT risk + save-desk"),
    ("COP-AU", "Authentication process miss", "Internal Failure", 22.00, 40.00, "QP01", "Re-verification time"),
    ("COP-CL", "Closing / next-step miss", "Internal Failure", 7.50, 15.00, "QP12 QP20", "Callback volume"),
    ("COP-RP", "Repeat-fail same attribute 30d", "Internal Failure", 45.00, 110.00, "Repeat Fail module", "Second QA pass + extra coaching"),
]


def main():
    SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        ROWS,
        columns=[
            "CopqRateKey", "DefectClass", "PafCategory",
            "InternalCostUsd", "ExternalCostUsd", "MapsToParameters", "CostLogic",
        ],
    )
    df["Currency"] = "USD"
    df["EffectiveFrom"] = "2025-01-01"
    df["IsActive"] = True
    df["TotalUnitCostUsd"] = df["InternalCostUsd"] + df["ExternalCostUsd"]
    df.to_csv(OUTPUT_FILE, index=False)
    print("SUCCESS")
    print(OUTPUT_FILE)
    print("Rows:", len(df))


if __name__ == "__main__":
    main()