import streamlit as st
import pandas as pd

st.title("TEG Data Viewer")

# Columns to drop
drop_cols = [
    "Location",
    "Device S/N",
    "Test Id",
    "Cartridge Type",
    "Printed Cartridge Lot",
    "Calculated Expiration Date",
    "Device Firmware",
    "Latest Note",
    "Additional Notes",
    "Segment",
    "Process"
]

# Columns for filtering
filter_cols = [
    "Device Name",
    "Sample Type",
    "Patient QC Result",
    "Test Status",
    "Username",
    "Test Name",
    "Test Information"
]

# Columns to prefix with Test Name
result_cols = [
    "Inhibition (%)",
    "Aggregation (%)",
    "R (min)",
    "MA (mm)",
    "LY30 (%)"
]

uploaded_file = st.file_uploader("Upload a TEG CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Drop unwanted columns
    df = df.drop(columns=[col for col in drop_cols if col in df.columns])

    # Convert date column
if "Date/Time Run" in df.columns:
    df["Date/Time Run"] = pd.to_datetime(df["Date/Time Run"])

    # Select date range
    start_date, end_date = st.date_input(
        "Select Date Range",
        [df["Date/Time Run"].min().date(), df["Date/Time Run"].max().date()]
    )

    # Select start & end time
    start_time = st.time_input("Start Time", value=df["Date/Time Run"].min().time())
    end_time = st.time_input("End Time", value=df["Date/Time Run"].max().time())

    # Combine date + time into datetime
    start_datetime = pd.Timestamp.combine(start_date, start_time)
    end_datetime = pd.Timestamp.combine(end_date, end_time)

    # Filter dataframe
    df = df[(df["Date/Time Run"] >= start_datetime) &
            (df["Date/Time Run"] <= end_datetime)]


    # Apply filters for categorical columns
    for col in filter_cols:
        if col in df.columns:
            options = df[col].dropna().unique().tolist()
            selected = st.multiselect(f"Filter by {col}", options)
            if selected:
                df = df[df[col].isin(selected)]

    # Show final filtered data
    st.dataframe(df)

    # --- Group and Export ---
    if st.button("Preview & Export Grouped Data"):
        # Separate result vs non-result columns
        id_cols = ["Date/Time Run", "Test Name"]
        numeric_subset = [c for c in result_cols if c in df.columns]
        text_subset = [c for c in df.columns if c not in id_cols + numeric_subset]

        # Melt only numeric result columns
        pivoted = df.melt(id_vars=id_cols, value_vars=numeric_subset,
                          var_name="Measure", value_name="Value")
        pivoted["Measure"] = pivoted["Test Name"] + "_" + pivoted["Measure"]

        # Pivot back wide
        wide_numeric = pivoted.pivot_table(
            index="Date/Time Run",
            columns="Measure",
            values="Value",
            aggfunc="first"
        )

        # Handle text/meta columns: keep first value
        wide_text = df.groupby("Date/Time Run")[text_subset].first()

        # Combine numeric + text
        grouped = pd.concat([wide_text, wide_numeric], axis=1).reset_index()

        # Define desired column renaming
        rename_map = {
            "CK_R (min)": "CK (min) R",
            "CK_MA (mm)": "CK (mm) MA",
            "CKH_R (min)": "CKH (min) R",
            "CKH_LY30 (%)": "CKH LY30%",
            "CRTH_MA (mm)": "CRTH (mm) MA",
            "CFFH_MA (mm)": "CFFH (mm) MA",
            "HKH_MA (mm)": "HKH (mm) MA",
            "ActF_MA (mm)": "ActF (mm) MA",
            "ADP_MA (mm)": "ADP (mm) MA",
            "ADP_Inhibition (%)": "ADP % Inhibition",
            "ADP_Aggregation (%)": "ADP % Aggregation",
            "AA_MA (mm)": "AA (mm) MA",
            "AA_Inhibition (%)": "AA % Inhibition",
            "AA_Aggregation (%)": "AA % Aggregation"
        }

        # Desired result order
        result_order = list(rename_map.values())

        # Apply renaming
        grouped = grouped.rename(columns=rename_map)

        # Reorder final columns
        final_cols = ["Date/Time Run"] + [c for c in grouped.columns if c not in result_order + ["Date/Time Run"]] + \
                     [c for c in result_order if c in grouped.columns]

        grouped = grouped[final_cols]

        # Show preview before export
        st.write("Preview of Grouped Data:", grouped.head())

        # Convert to CSV for download
        csv = grouped.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Grouped CSV",
            data=csv,
            file_name="TEG_grouped.csv",
            mime="text/csv"
        )
