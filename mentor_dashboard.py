import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Page title

st.title("Youth Hours Dashboard")

st.write("This dashboard is designed to help you track and view your worked hours and summary payment")

# Load CSV data

timesheet_df = pd.read_csv("Consolidated - Masi Youth Hours May_June 2026 - Timesheet.csv")
hours_df = pd.read_csv("Consolidated - Masi Youth Hours May_June 2026 - Hours.csv")

# Normalize IDs so merge keys always have consistent type/format.
def normalize_employee_id(series):
    normalized = (
        pd.to_numeric(series, errors="coerce")
        .astype("Int64")
        .astype(str)
        .replace("<NA>", np.nan)
    )
    return normalized

timesheet_df["Employee ID"] = normalize_employee_id(timesheet_df["Employee ID"])
hours_df["Employee ID"] = normalize_employee_id(hours_df["Employee ID"])

# Find check in and check out columns (timesheet only)
check_in_columns = [
    col for col in timesheet_df.columns
    if "Check in" in col
]

check_out_columns = [
    col for col in timesheet_df.columns
    if "Check out" in col or "Check-out" in col
]

# Stop attendance calculations/display at this column so future days are excluded.
ATTENDANCE_END_COLUMN = "5 June Check out"
if ATTENDANCE_END_COLUMN in check_out_columns:
    end_idx = check_out_columns.index(ATTENDANCE_END_COLUMN) + 1
    check_in_columns = check_in_columns[:end_idx]
    check_out_columns = check_out_columns[:end_idx]

# Merge job metadata and official totals from Hours into Timesheet
df = timesheet_df.merge(
    hours_df[[
        "Employee ID",
        "Job Title",
        "Site Type",
        "Rate",
        "Total no. of hours",
        "Total no. of days",
        "Amount Owed",
    ]],
    on="Employee ID",
    how="left",
)

JOB_CAPS = {
    "EduTech Coach": 3.5,
    "1000 Stories Youth": 3.5,
    "Homework Coach": 4.0,
    "Numeracy Coach": 4.0,
    "Practitioner": 6.0,
    "ZZ ECD Coach": 3.5,
    "Zazi Izandi Coach": 3.5,
    "Literacy Coach ECD": 5,
}

LITERACY_TITLES = {"Literacy Coach", "Literacy Coaches (ZZ)"}


def parse_amount_owed(value):
    try:
        return float(str(value).replace("R", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0

# Calculate hours fuction

def calculate_hours(check_in, check_out):

    try:

        time_in = datetime.strptime(str(check_in), "%H:%M")
        time_out = datetime.strptime(str(check_out), "%H:%M")

        hours = (time_out - time_in).seconds / 3600

        return round(hours, 1)

    except:
        
        return 0

def get_hour_cap(job_title, site_type):

    if job_title in LITERACY_TITLES:
        site = str(site_type).strip()
        if site == "Primary Schools":
            return 4.5
        if site == "ECDCs":
            return 5.5

    return JOB_CAPS.get(job_title)       

#  Process Youth Data
total_hours_list = []
missing_days_list = []
total_days_list = []

for index, row in df.iterrows():

    job_title = row["Job Title"]
    site_type = row["Site Type"]

    hour_cap = get_hour_cap(job_title, site_type)
    
    total_hours = 0
    missing_days = []
    total_days = 0

    for in_col, out_col in zip(check_in_columns, check_out_columns):

        check_in = row[in_col]
        check_out = row[out_col]

        # Missing day check

        if pd.isna(check_in) or pd.isna(check_out):
            day_name = in_col.replace(" Check in", "")
            missing_days.append(day_name)

        # Calculate hours
        hours = calculate_hours(check_in, check_out)

        # Apply daily cap before totalling
        if hour_cap is not None and hours > 0:
            hours = min(hours, hour_cap)

        total_hours += hours

        if hours > 0:
            total_days += 1

    total_hours_list.append(round(total_hours, 1))
    missing_days_list.append(", ".join(missing_days))
    total_days_list.append(total_days)


# ADD Totals
# df["Total Hours"] = total_hours_list
df["Total Days Worked"] = total_days_list

df["Capped Hours"] = total_hours_list

df["Total Pay"] = round(
    df["Capped Hours"] * df["Rate"],
    2
)

df["Official Hours"] = pd.to_numeric(df["Total no. of hours"], errors="coerce")
df["Official Days"] = pd.to_numeric(df["Total no. of days"], errors="coerce")
df["Official Pay"] = df["Amount Owed"].apply(parse_amount_owed)

df["Missing Days"] = missing_days_list

# Youth Login/Selection

mentor_options = sorted(df["Mentor"].dropna().unique())
selected_mentor = st.selectbox("Select Mentor", mentor_options)

mentor_filtered_df = df[df["Mentor"] == selected_mentor]
if mentor_filtered_df.empty:
    st.error("No timesheet data found for that mentor.")
    st.stop()

employee_name = st.selectbox(
    "Select Your Employee Name",
    sorted(mentor_filtered_df["Full Name"].dropna().unique())
)

# Show only that employee
employee_data = mentor_filtered_df[mentor_filtered_df["Full Name"] == employee_name]

if employee_data.empty:
    st.error("No timesheet data found for that employee name.")
    st.stop()

employee = employee_data.iloc[0]

# Display Summary

st.subheader("Your Summary")

col1, col2 = st.columns(2)
with col1:
    st.write(f"**Job Title:** {employee['Job Title']}")
    st.write(f"**Site Type:** {employee['Site Type']}")
with col2:
    st.write(f"**Hourly Rate:** R {employee['Rate']:.2f}")

# st.metric(
    # "Calculated Hours (from timesheet)",
    # f"{employee['Capped Hours']:.1f} hrs",
    # help="Hours calculated from your check-in/out times with daily caps applied.",
# )

official_hours = employee["Official Hours"]
if pd.notna(official_hours):
    hours_delta = round(employee["Capped Hours"] - official_hours, 1)
    st.metric(
        "Calculated Hours",
        f"{official_hours:.1f} hrs"
    )

# st.metric(
    # "Estimated Pay (calculated)",
    # f"R {employee['Total Pay']:,.2f}",
# )

official_pay = employee["Official Pay"]
if official_pay > 0:
    pay_delta = round(employee["Total Pay"] - official_pay, 2)
    st.metric(
        "Estimated Amount Owed to date",
        f"R {official_pay:,.2f}",
        # delta=f"R {pay_delta:+,.2f} vs calculated" if pay_delta != 0 else None,
    )

# st.metric(
    # "Total Days Worked (calculated)",
    # employee["Total Days Worked"],
# )

official_days = employee["Official Days"]
if pd.notna(official_days):
    st.metric(
        "Total Days Worked",
        int(official_days),
    )

# Warning Section
if employee["Missing Days"] != "" or employee["Check In"] == employee["Check Out"]:
    st.error(
        f"WARNING: Missing check-in/out for {employee['Missing Days']} or check-in/out is the same"
    )

# Show Daily Details
st.subheader("Daily Attendance")

attendance_data = []
for in_col, out_col in zip(check_in_columns, check_out_columns):

    day = in_col.replace(" Check in", "")

    attendance_data.append({

        "Day" : day,
        "Check In" : employee[in_col],
        "Check Out": employee[out_col]

    })

attendance_df = pd.DataFrame(attendance_data)

# Colour missing days

def highlight_rows(row):

    if pd.isna(row["Check In"]) or pd.isna(row["Check Out"]) or row["Check In"] == row["Check Out"]:

        return ["background-color: pink"] * len(row)

    return [""] * len(row)

styled_table_df = attendance_df.style.apply(
    highlight_rows, axis=1)

st.dataframe(styled_table_df)

# st.error("N.B. IF YOU DO NOT SYNC DAILY, YOUR UNSYNCED HOURS WILL NOT REFLECT ON THE APP")























































































































































































































































































































































































































































































































































































































































































































































































































































































































































