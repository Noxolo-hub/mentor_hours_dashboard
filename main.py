import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Page title

st.title("Youth Hours Dashboard")

st.write("This dashboard is designed to help you track and view your worked hours and summary payment")

# Load CSV data

df = pd.read_csv("Consolidated - Masi Youth Hours Apr_May 2026 - Timesheet.csv")

# Find check in and check out columns
check_in_columns = [
    col for col in df.columns
    if "Check in" in col
]

check_out_columns = [
    col for col in df.columns
    if "Check out" in col or "Check-out" in col
]

# Calculate hours fuction

def calculate_hours(check_in, check_out):

    try:

        time_in = datetime.strptime(str(check_in), "%H:%M")
        time_out = datetime.strptime(str(check_out), "%H:%M")

        hours = (time_out - time_in).seconds / 3600

        return round(hours, 1)

    except:
        
        return 0

#  Process Youth Data
total_hours_list = []
missing_days_list = []
total_days_list = []

for index, row in df.iterrows():
    
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
        total_hours += hours

        # Count work days
        if hours > 0:
            total_days += 1

    total_hours_list.append(total_hours)
    missing_days_list.append(", ".join(missing_days))
    total_days_list.append(total_days)


# ADD Totals
df["Total Hours"] = total_hours_list
df["Total Days Worked"] = total_days_list

hourly_rate = 32.01

df["Total Pay"] = round(df["Total Hours"] * hourly_rate, 2)

df["Total Hours"] = round(df["Total Hours"], 1)

df["Missing Days"] = missing_days_list

# Youth Login/Selection

employee_id = st.selectbox(
    "Select Your Employee ID",
    sorted(df["Employee ID"].dropna().unique())
)

# Show only that employee
employee_data = df[df["Employee ID"] == employee_id]

if employee_data.empty:
    st.error("No timesheet data found for that employee ID.")
    st.stop()

employee = employee_data.iloc[0]

# Display Summary

st.subheader("Your Summary")

st.metric(
    "Total Hours Worked",
    f"{round(employee['Total Hours'], 1)} hrs")

st.metric(
    "Estimated Pay thus far",
    f"{round(employee['Total Pay'], 2)}"
)

st.metric(
"Total Days Worked",
employee["Total Days Worked"]
)

# Warning Section
if employee["Missing Days"] != "":
    st.error(
        f"WARNING: Missing check-in/out for {employee['Missing Days']}"
    )

else:
    st.success("No missing attendance records")  

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

    if pd.isna(row["Check In"]) or pd.isna(row["Check Out"]):

        return ["background-color: pink"] * len(row)

    return [""] * len(row)

styled_table = attendance_df.style.apply(
        highlight_rows, axis=1)

st.dataframe(styled_table)



























































































































































































































































































































































































































































































































































































































































































































































































































































































































































