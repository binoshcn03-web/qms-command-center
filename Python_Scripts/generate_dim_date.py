"""
Dim_Date generator — ONE file only.
Creates Dim_Date.csv in the same folder as this script.
"""

from pathlib import Path

import numpy as np
import pandas as pd

CALENDAR_START = "2025-01-01"
CALENDAR_END = "2026-08-31"
FISCAL_YEAR_START_MONTH = 4
AS_OF_DATE = pd.Timestamp("2026-09-08")

SAVE_FOLDER = Path(__file__).resolve().parent.parent / "Data_Source"
OUTPUT_FILE = SAVE_FOLDER / "Dim_Date.csv"
SAVE_FOLDER.mkdir(parents=True, exist_ok=True)


def holiday_calendar():
    rows = [
        ("2025-01-26", "Republic Day", "IN"),
        ("2025-03-14", "Holi", "IN"),
        ("2025-03-31", "Eid ul-Fitr", "IN"),
        ("2025-08-15", "Independence Day", "IN"),
        ("2025-10-02", "Gandhi Jayanti", "IN"),
        ("2025-10-21", "Diwali", "IN"),
        ("2025-12-25", "Christmas", "IN"),
        ("2026-01-26", "Republic Day", "IN"),
        ("2026-03-04", "Holi", "IN"),
        ("2026-03-21", "Eid ul-Fitr", "IN"),
        ("2026-08-15", "Independence Day", "IN"),
        ("2026-10-02", "Gandhi Jayanti", "IN"),
        ("2026-11-08", "Diwali", "IN"),
        ("2026-12-25", "Christmas", "IN"),
        ("2025-01-01", "New Year", "PH"),
        ("2025-02-25", "EDSA People Power", "PH"),
        ("2025-04-17", "Maundy Thursday", "PH"),
        ("2025-04-18", "Good Friday", "PH"),
        ("2025-06-12", "Independence Day", "PH"),
        ("2025-08-25", "National Heroes Day", "PH"),
        ("2025-11-30", "Bonifacio Day", "PH"),
        ("2025-12-25", "Christmas", "PH"),
        ("2025-12-30", "Rizal Day", "PH"),
        ("2026-01-01", "New Year", "PH"),
        ("2026-02-25", "EDSA People Power", "PH"),
        ("2026-04-02", "Maundy Thursday", "PH"),
        ("2026-04-03", "Good Friday", "PH"),
        ("2026-06-12", "Independence Day", "PH"),
        ("2026-08-31", "National Heroes Day", "PH"),
        ("2026-11-30", "Bonifacio Day", "PH"),
        ("2026-12-25", "Christmas", "PH"),
        ("2026-12-30", "Rizal Day", "PH"),
        ("2025-01-01", "Año Nuevo", "CO"),
        ("2025-01-06", "Reyes Magos", "CO"),
        ("2025-05-01", "Día del Trabajo", "CO"),
        ("2025-07-20", "Independencia", "CO"),
        ("2025-08-07", "Batalla de Boyacá", "CO"),
        ("2025-12-08", "Inmaculada Concepción", "CO"),
        ("2025-12-25", "Navidad", "CO"),
        ("2026-01-01", "Año Nuevo", "CO"),
        ("2026-01-12", "Reyes Magos", "CO"),
        ("2026-05-01", "Día del Trabajo", "CO"),
        ("2026-07-20", "Independencia", "CO"),
        ("2026-08-07", "Batalla de Boyacá", "CO"),
        ("2026-12-08", "Inmaculada Concepción", "CO"),
        ("2026-12-25", "Navidad", "CO"),
    ]
    hol = pd.DataFrame(rows, columns=["FullDate", "HolidayName", "HolidayCountry"])
    hol["FullDate"] = pd.to_datetime(hol["FullDate"])
    return hol


def fiscal_year_label(dates, start_month):
    fy_end_year = pd.Series(
        np.where(dates.dt.month >= start_month, dates.dt.year + 1, dates.dt.year),
        index=dates.index,
    )
    fy_start_year = fy_end_year - 1
    return "FY" + fy_start_year.astype(str) + "-" + fy_end_year.astype(str).str[-2:]


def build_dim_date():
    d = pd.DataFrame({"FullDate": pd.date_range(CALENDAR_START, CALENDAR_END, freq="D")})

    d["DateKey"] = d["FullDate"].dt.strftime("%Y%m%d").astype(int)
    d["Year"] = d["FullDate"].dt.year
    d["QuarterNumber"] = d["FullDate"].dt.quarter
    d["YearQuarter"] = d["Year"].astype(str) + "-Q" + d["QuarterNumber"].astype(str)
    d["MonthNumber"] = d["FullDate"].dt.month
    d["MonthName"] = d["FullDate"].dt.month_name()
    d["MonthNameShort"] = d["FullDate"].dt.strftime("%b")
    d["YearMonth"] = d["FullDate"].dt.strftime("%Y-%m")
    d["YearMonthName"] = d["FullDate"].dt.strftime("%Y-%b")
    d["DayOfMonth"] = d["FullDate"].dt.day
    d["DayOfYear"] = d["FullDate"].dt.dayofyear
    d["DayName"] = d["FullDate"].dt.day_name()
    d["DayNameShort"] = d["FullDate"].dt.strftime("%a")
    d["DayOfWeekIso"] = d["FullDate"].dt.dayofweek + 1
    d["IsWeekend"] = d["DayOfWeekIso"].isin([6, 7])

    iso = d["FullDate"].dt.isocalendar()
    d["IsoYear"] = iso["year"].astype(int)
    d["IsoWeek"] = iso["week"].astype(int)
    d["IsoYearWeek"] = d["IsoYear"].astype(str) + "-W" + d["IsoWeek"].astype(str).str.zfill(2)
    d["WeekStartDate"] = d["FullDate"] - pd.to_timedelta(d["DayOfWeekIso"] - 1, unit="D")
    d["WeekEndDate"] = d["WeekStartDate"] + pd.Timedelta(days=6)

    d["FiscalYearLabel"] = fiscal_year_label(d["FullDate"], FISCAL_YEAR_START_MONTH)
    d["FiscalMonthNumber"] = ((d["MonthNumber"] - FISCAL_YEAR_START_MONTH) % 12) + 1
    d["FiscalQuarterNumber"] = ((d["FiscalMonthNumber"] - 1) // 3) + 1
    d["FiscalYearQuarter"] = d["FiscalYearLabel"] + "-FQ" + d["FiscalQuarterNumber"].astype(str)

    hol = (
        holiday_calendar()
        .groupby("FullDate", as_index=False)
        .agg(
            HolidayName=("HolidayName", lambda s: " | ".join(sorted(set(s)))),
            HolidayCountries=("HolidayCountry", lambda s: ",".join(sorted(set(s)))),
        )
    )
    d = d.merge(hol, on="FullDate", how="left")
    d["IsHoliday"] = d["HolidayName"].notna()
    d["HolidayName"] = d["HolidayName"].fillna("")
    d["HolidayCountries"] = d["HolidayCountries"].fillna("")
    d["IsWorkingDay"] = (~d["IsWeekend"]) & (~d["IsHoliday"])

    as_of = AS_OF_DATE.normalize()
    d["AsOfDate"] = as_of
    d["IsCurrentMonth"] = (d["Year"] == as_of.year) & (d["MonthNumber"] == as_of.month)
    d["IsCurrentYear"] = d["Year"] == as_of.year
    d["IsCurrentFiscalYear"] = d["FiscalYearLabel"] == fiscal_year_label(
        pd.Series([as_of]), FISCAL_YEAR_START_MONTH
    ).iloc[0]
    d["IsFutureDate"] = d["FullDate"] > as_of
    d["DaysFromAsOf"] = (d["FullDate"] - as_of).dt.days
    d["MonthIndex"] = (d["Year"] - pd.Timestamp(CALENDAR_START).year) * 12 + (
        d["MonthNumber"] - pd.Timestamp(CALENDAR_START).month
    )
    d["DateIndex"] = np.arange(1, len(d) + 1)
    d["SamplingPeriodMonth"] = d["YearMonth"]
    d["SamplingPeriodWeek"] = d["IsoYearWeek"]
    return d


def main():
    dim = build_dim_date()
    dim.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d")
    print("SUCCESS")
    print("File created:")
    print(OUTPUT_FILE)
    print("Rows:", len(dim))
    print("From:", dim["FullDate"].min().date(), "To:", dim["FullDate"].max().date())


if __name__ == "__main__":
    main()