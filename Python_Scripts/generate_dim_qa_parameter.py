"""
Dim_QA_Parameter generator — ONE file only.
Creates Dim_QA_Parameter.csv in the sibling Data_Source folder.

Grain: one row = one quality parameter on the Amazon CX evaluation form.
Aligned to BEST QM V24.1:
  - Customer Critical Accuracy target 95%
  - Business Critical Accuracy target 90%
  - Compliance Critical Accuracy target 99.5%
  - Rider attributes do not change the client score
  - Any fail on CC / BC / CompC fails the interaction
"""

from pathlib import Path

import pandas as pd

SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Dim_QA_Parameter.csv"

FORM_VERSION = "AMZ-EOF-v1.0"
EFFECTIVE_FROM = "2025-01-01"

# 20 parameters. Client weights sum to 100. Riders are weight 0 on the client score.
PARAMETERS = [
    # Compliance Critical — BEST QM CompC Accuracy 99.5%. GDPR / privacy examples are in the PDF.
    {
        "ParameterID": "QP-01",
        "ParameterName": "Security verification and authentication",
        "Category": "Authentication",
        "CriticalityType": "Compliance Critical",
        "WeightPctClient": 8,
        "WeightPctInternal": 8,
        "IsZeroTolerance": True,
        "IsPrivacySensitive": True,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Compliance",
        "CopqClassHint": "COP-FT",
        "QualityFocus": "Authentication",
        "AmazonFailExample": "Account opened or refund processed without OTP / security check",
        "BestQmNote": "Security verification is cited as a compliance-style control in BEST QM data-collection guidance",
    },
    {
        "ParameterID": "QP-02",
        "ParameterName": "Privacy, PII and GDPR handling",
        "Category": "Compliance",
        "CriticalityType": "Compliance Critical",
        "WeightPctClient": 8,
        "WeightPctInternal": 8,
        "IsZeroTolerance": True,
        "IsPrivacySensitive": True,
        "IsGdprRelevant": True,
        "IshikawaPillar": "Compliance",
        "CopqClassHint": "COP-PR",
        "QualityFocus": "Compliance",
        "AmazonFailExample": "Read full card number, shipping address of another household member, or Rx details aloud",
        "BestQmNote": "BEST QM CompC examples explicitly include GDPR errors and privacy errors",
    },
    {
        "ParameterID": "QP-03",
        "ParameterName": "Payment, gift-card and refund integrity",
        "Category": "Compliance",
        "CriticalityType": "Compliance Critical",
        "WeightPctClient": 8,
        "WeightPctInternal": 8,
        "IsZeroTolerance": True,
        "IsPrivacySensitive": True,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Compliance",
        "CopqClassHint": "COP-FT",
        "QualityFocus": "Resolution / SOP",
        "AmazonFailExample": "Refund to an unverified wallet, gift-card code spoken in full, or duplicate capture left unflagged",
        "BestQmNote": "Financial mishandling is a compliance-critical / zero-tolerance miss on this Amazon SOW",
    },
    {
        "ParameterID": "QP-04",
        "ParameterName": "Mandatory policy and regulatory disclosure",
        "Category": "Compliance",
        "CriticalityType": "Compliance Critical",
        "WeightPctClient": 7,
        "WeightPctInternal": 7,
        "IsZeroTolerance": True,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Compliance",
        "CopqClassHint": "COP-FT",
        "QualityFocus": "Compliance",
        "AmazonFailExample": "Pharmacy item shipped without Rx rule stated, or age-restricted handoff skipped",
        "BestQmNote": "BEST QM CompC = national / state / federal or industry-body compliance",
    },
    # Customer Critical — BEST QM CC Accuracy 95%. Wrong info, rudeness, not resolving.
    {
        "ParameterID": "QP-05",
        "ParameterName": "Correct issue identification",
        "Category": "Discovery",
        "CriticalityType": "Customer Critical",
        "WeightPctClient": 6,
        "WeightPctInternal": 6,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-RS",
        "QualityFocus": "Process / Discovery",
        "AmazonFailExample": "Treated a 'delivered missing' as a simple delay and never opened A-to-z / investigation path",
        "BestQmNote": "Customer-critical errors include not resolving the customer issue",
    },
    {
        "ParameterID": "QP-06",
        "ParameterName": "Accurate resolution and SOP application",
        "Category": "Resolution",
        "CriticalityType": "Customer Critical",
        "WeightPctClient": 8,
        "WeightPctInternal": 8,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-RS",
        "QualityFocus": "Resolution / SOP",
        "AmazonFailExample": "Promised prepaid return on a final-sale item, or denied a Prime missed-promise path that SOP allows",
        "BestQmNote": "Wrong information is a listed Customer Critical error",
    },
    {
        "ParameterID": "QP-07",
        "ParameterName": "Complete resolution / FCR attempt",
        "Category": "Resolution",
        "CriticalityType": "Customer Critical",
        "WeightPctClient": 7,
        "WeightPctInternal": 7,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-RS",
        "QualityFocus": "Resolution / SOP",
        "AmazonFailExample": "Closed the contact after creating a ticket with no action, customer must call back for the refund",
        "BestQmNote": "Contact Resolution is a BEST QM metric; incomplete resolution is a CC miss",
    },
    {
        "ParameterID": "QP-08",
        "ParameterName": "Courtesy, empathy and no rudeness",
        "Category": "Soft Skills",
        "CriticalityType": "Customer Critical",
        "WeightPctClient": 6,
        "WeightPctInternal": 7,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "People",
        "CopqClassHint": "COP-SS",
        "QualityFocus": "Soft Skills",
        "AmazonFailExample": "Interrupted, blamed the customer for a carrier delay, or used sarcastic tone on a DSAT-risk contact",
        "BestQmNote": "Mistreating the customer / rudeness is a listed Customer Critical example",
    },
    {
        "ParameterID": "QP-09",
        "ParameterName": "Ownership and contact control",
        "Category": "Soft Skills",
        "CriticalityType": "Customer Critical",
        "WeightPctClient": 5,
        "WeightPctInternal": 5,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "People",
        "CopqClassHint": "COP-SS",
        "QualityFocus": "Soft Skills",
        "AmazonFailExample": "Transferred without recap, or ended the chat while the customer was still typing the order ID",
        "BestQmNote": "Customer-critical experience impact; also feeds EOF / TOPS coaching",
    },
    {
        "ParameterID": "QP-10",
        "ParameterName": "Correct information and no wrong commitment",
        "Category": "Resolution",
        "CriticalityType": "Customer Critical",
        "WeightPctClient": 6,
        "WeightPctInternal": 6,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-RS",
        "QualityFocus": "Resolution / SOP",
        "AmazonFailExample": "Quoted same-day replacement on a seller-fulfilled item that cannot be advanced-replaced",
        "BestQmNote": "Wrong information is a Customer Critical error in BEST QM 2.4",
    },
    {
        "ParameterID": "QP-11",
        "ParameterName": "Escalation accuracy",
        "Category": "Resolution",
        "CriticalityType": "Customer Critical",
        "WeightPctClient": 5,
        "WeightPctInternal": 5,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-RS",
        "QualityFocus": "Resolution / SOP",
        "AmazonFailExample": "Sent a pharmacy cold-chain fail to general returns instead of urgent pharmacy queue",
        "BestQmNote": "BEST QM Escalation Accuracy target >90%",
    },
    {
        "ParameterID": "QP-12",
        "ParameterName": "Expectation setting and next steps",
        "Category": "Closing",
        "CriticalityType": "Customer Critical",
        "WeightPctClient": 5,
        "WeightPctInternal": 5,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-CL",
        "QualityFocus": "Process / Discovery",
        "AmazonFailExample": "No refund timeline, no tracking of the investigation, customer left without a case ID",
        "BestQmNote": "Drives Contact Resolution and CSAT correlation required in CX analysis",
    },
    # Business Critical — BEST QM BC Accuracy 90%. Wrong documentation, missed process.
    {
        "ParameterID": "QP-13",
        "ParameterName": "CRM and case documentation completeness",
        "Category": "Documentation",
        "CriticalityType": "Business Critical",
        "WeightPctClient": 5,
        "WeightPctInternal": 5,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-DC",
        "QualityFocus": "Resolution / SOP",
        "AmazonFailExample": "No order ID, no A-to-z claim number, no promised callback time in the case",
        "BestQmNote": "Wrong / missing documentation is a listed Business Critical example",
    },
    {
        "ParameterID": "QP-14",
        "ParameterName": "TCD and reason-code accuracy",
        "Category": "Documentation",
        "CriticalityType": "Business Critical",
        "WeightPctClient": 4,
        "WeightPctInternal": 4,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-DC",
        "QualityFocus": "Process / Discovery",
        "AmazonFailExample": "Coded a refund-not-initiated contact as Delivery Delay, breaking TCD mix analysis",
        "BestQmNote": "Required for BEST QM Top Contact Driver analysis",
    },
    {
        "ParameterID": "QP-15",
        "ParameterName": "Knowledge-base and tool adherence",
        "Category": "Process",
        "CriticalityType": "Business Critical",
        "WeightPctClient": 4,
        "WeightPctInternal": 5,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-DC",
        "QualityFocus": "Resolution / SOP",
        "AmazonFailExample": "Used memory for a returns window instead of the live policy article",
        "BestQmNote": "PHAROS example in BEST QM Repeat Fail: top failed attribute is KB adherence",
    },
    {
        "ParameterID": "QP-16",
        "ParameterName": "Hold, mute and transfer protocol",
        "Category": "Process",
        "CriticalityType": "Business Critical",
        "WeightPctClient": 3,
        "WeightPctInternal": 3,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-DC",
        "QualityFocus": "Process / Discovery",
        "AmazonFailExample": "Silent hold over 60 seconds with no permission, or cold transfer to seller desk",
        "BestQmNote": "Business process adherence; also an EOF observable behavior",
    },
    {
        "ParameterID": "QP-17",
        "ParameterName": "Disposition and wrap-up accuracy",
        "Category": "Documentation",
        "CriticalityType": "Business Critical",
        "WeightPctClient": 3,
        "WeightPctInternal": 3,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-DC",
        "QualityFocus": "Process / Discovery",
        "AmazonFailExample": "Marked Resolved when refund was only promised, inflating Contact Resolution",
        "BestQmNote": "Protects Contact Resolution and Success Rate measurement integrity",
    },
    {
        "ParameterID": "QP-18",
        "ParameterName": "Required offer / process path (Prime, replacement, A-to-z)",
        "Category": "Process",
        "CriticalityType": "Business Critical",
        "WeightPctClient": 2,
        "WeightPctInternal": 3,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "Process",
        "CopqClassHint": "COP-RS",
        "QualityFocus": "Resolution / SOP",
        "AmazonFailExample": "Did not offer A-to-z when seller went silent past SLA",
        "BestQmNote": "BEST QM BC example includes missed required process / offer steps",
    },
    # Rider — collected for EOF / TOPS coaching. Do not change client score.
    {
        "ParameterID": "QP-19",
        "ParameterName": "Opening, branding and purpose statement",
        "Category": "Opening",
        "CriticalityType": "Rider",
        "WeightPctClient": 0,
        "WeightPctInternal": 3,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "People",
        "CopqClassHint": "COP-SS",
        "QualityFocus": "Soft Skills",
        "AmazonFailExample": "No Amazon branding, no name, jumped to troubleshooting",
        "BestQmNote": "Rider attribute: internal tracking / EOF, does not change client scoring methodology",
    },
    {
        "ParameterID": "QP-20",
        "ParameterName": "Closing recap and survey invite",
        "Category": "Closing",
        "CriticalityType": "Rider",
        "WeightPctClient": 0,
        "WeightPctInternal": 3,
        "IsZeroTolerance": False,
        "IsPrivacySensitive": False,
        "IsGdprRelevant": False,
        "IshikawaPillar": "People",
        "CopqClassHint": "COP-CL",
        "QualityFocus": "Soft Skills",
        "AmazonFailExample": "Dropped the chat after refund with no recap and no CSAT invite",
        "BestQmNote": "Rider attribute on the EOF; supports coaching, not client score",
    },
]


def build():
    df = pd.DataFrame(PARAMETERS)
    df["FormVersion"] = FORM_VERSION
    df["EffectiveFrom"] = pd.to_datetime(EFFECTIVE_FROM)
    df["EffectiveTo"] = pd.NaT
    df["IsActive"] = True
    df["ScoringType"] = "Binary_PassFail"
    df["PassThresholdPct"] = 100
    df["IsCritical"] = df["CriticalityType"].isin(
        ["Customer Critical", "Business Critical", "Compliance Critical"]
    )
    df["IsFatal"] = df["CriticalityType"].eq("Compliance Critical")
    df["FailInteractionOnFail"] = df["IsCritical"]
    df["RepeatFailEligible"] = True
    df["ClientScoreAffecting"] = df["WeightPctClient"] > 0
    df["TargetAccuracyPct"] = df["CriticalityType"].map(
        {
            "Customer Critical": 0.95,
            "Business Critical": 0.90,
            "Compliance Critical": 0.995,
            "Rider": pd.NA,
        }
    )
    df["BestQmKpi"] = df["CriticalityType"].map(
        {
            "Customer Critical": "Customer Critical Accuracy",
            "Business Critical": "Business Critical Accuracy",
            "Compliance Critical": "Compliance Critical Accuracy",
            "Rider": "EOF / Rider (not a BEST QM score KPI)",
        }
    )
    df["SortOrder"] = range(1, len(df) + 1)

    client_w = int(df["WeightPctClient"].sum())
    if client_w != 100:
        raise ValueError(f"Client weights must sum to 100, got {client_w}")
    if len(df) != 20:
        raise ValueError(f"Expected 20 parameters, got {len(df)}")

    ordered = [
        "ParameterID",
        "FormVersion",
        "ParameterName",
        "Category",
        "CriticalityType",
        "BestQmKpi",
        "TargetAccuracyPct",
        "WeightPctClient",
        "WeightPctInternal",
        "ClientScoreAffecting",
        "IsCritical",
        "IsFatal",
        "IsZeroTolerance",
        "FailInteractionOnFail",
        "IsPrivacySensitive",
        "IsGdprRelevant",
        "ScoringType",
        "PassThresholdPct",
        "RepeatFailEligible",
        "IshikawaPillar",
        "CopqClassHint",
        "QualityFocus",
        "AmazonFailExample",
        "BestQmNote",
        "EffectiveFrom",
        "EffectiveTo",
        "IsActive",
        "SortOrder",
    ]
    return df[ordered]


def main():
    SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
    dim = build()
    dim.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d")
    print("SUCCESS")
    print("File created:")
    print(OUTPUT_FILE)
    print("Rows:", len(dim))
    print(dim.groupby("CriticalityType").size().to_string())
    print("Client weight sum:", int(dim["WeightPctClient"].sum()))
    print("Fatal / zero-tolerance:", int(dim["IsFatal"].sum()))


if __name__ == "__main__":
    main()