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
        # No need to convert twice
        # df["Date/Time Run"] = pd.to_datetime(df["Date/Time Run"])

    # Let user pick date range (can be 1 or 2 dates)
    date_range = st.date_input(
        "Select Date Range",
        value=(df["Date/Time Run"].min().date(), df["Date/Time Run"].max().date())
    )

    # Show time pickers
    start_time = st.time_input("Start Time", value=df["Date/Time Run"].min().time())
    end_time = st.time_input("End Time", value=df["Date/Time Run"].max().time())

    # Apply filter only if 2 dates are selected
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
        start_datetime = pd.Timestamp.combine(start_date, start_time)
        end_datetime = pd.Timestamp.combine(end_date, end_time)

        df = df[(df["Date/Time Run"] >= start_datetime) &
                (df["Date/Time Run"] <= end_datetime)]


    # Apply filters for categorical columns
    for col in filter_cols:
        if col in df.columns:
            options = df[col].dropna().unique().tolist()
            selected = st.multiselect(f"Filter by {col}", options)
            if selected:
                df = df[df[col].isin(selected)]
    
    df.index = df.index + 1  # Start index from 1 for display
    # Show final filtered data
    st.dataframe(df)

    # --- Group and Export ---
    if st.button("Reorganize Data"):
        # Separate result vs non-result columns
        # Include "Device Name" in id_cols for grouping
        id_cols = ["Device Name", "Date/Time Run", "Test Name"]
        numeric_subset = [c for c in result_cols if c in df.columns]
        text_subset = [c for c in df.columns if c not in id_cols + numeric_subset]

        # Melt only numeric result columns
        pivoted = df.melt(id_vars=id_cols, value_vars=numeric_subset,
                          var_name="Measure", value_name="Value")
        pivoted["Measure"] = pivoted["Test Name"] + "_" + pivoted["Measure"]

        # Pivot back wide, using "Device Name" and "Date/Time Run" as index
        wide_numeric = pivoted.pivot_table(
            index=["Device Name", "Date/Time Run"],
            columns="Measure",
            values="Value",
            aggfunc="first"
        )

        # Handle text/meta columns: keep first value, group by "Device Name" and "Date/Time Run"
        wide_text = df.groupby(["Device Name", "Date/Time Run"])[text_subset].first()

        # Combine numeric + text
        # Ensure index is aligned for concatenation
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

        # Reorder final columns - ensure "Device Name" is included
        final_cols = ["Device Name", "Date/Time Run"] + [c for c in grouped.columns if c not in result_order + ["Device Name", "Date/Time Run"]] + \
                     [c for c in result_order if c in grouped.columns]

        grouped = grouped[final_cols]


        # --- Highlight out-of-range values in grouped data ---
        # Default to L1, if Sample Type is not L1 then use L2
        grouped_ranges_by_sample = {
            "L1": {
                "CK (min) R": (5.2, 7.6),
                "CK (mm) MA": (64, 69),
                "CKH (min) R": (3.6, 6.8),
                "CKH LY30%": (0, 0),
                "CRTH (mm) MA": (59, 64),
                "CFFH (mm) MA": (59, 66),
                "HKH (mm) MA": (53, 68),
                "ActF (mm) MA": (2, 19),
                "ADP (mm) MA": (45, 69),
                "ADP % Inhibition": (0, 17),
                "ADP % Aggregation": (83, 100),
                "AA (mm) MA": (51, 71),
                "AA % Inhibition": (0, 11),
                "AA % Aggregation": (89, 100)
            },
            "L2": {
                "CK (min) R": (1, 1.5),
                "CK (mm) MA": (22, 31),
                "CKH (min) R": (1, 1.5),
                "CKH LY30%": (91, 94),
                "CRTH (mm) MA": (22, 33),
                "CFFH (mm) MA": (22, 32),
                "HKH (mm) MA": (53, 68),
                "ActF (mm) MA": (2, 19),
                "ADP (mm) MA": (45, 69),
                "ADP % Inhibition": (0, 17),
                "ADP % Aggregation": (83, 100),
                "AA (mm) MA": (51, 71),
                "AA % Inhibition": (0, 11),
                "AA % Aggregation": (89, 100)
            }
        }

        def get_range_key_for_row(row):
            # Default to L1, if Sample Type is not L1 then use L2
            if "Sample Type" in row and str(row["Sample Type"]).strip() == "L1":
                return "L1"
            return "L2"

        def highlight_grouped(val, col, range_key):
            try:
                v = float(val)
                # Round the value to 1 decimal place
                v_rounded = round(v, 1)
                ranges = grouped_ranges_by_sample.get(range_key, grouped_ranges_by_sample["L1"])
                low, high = ranges.get(col, (None, None))
                if low is not None and high is not None and (v_rounded < low or v_rounded > high):
                    return "color: red"
            except Exception:
                pass
            return ""

        def highlight_grouped_dataframe(grouped):
            styled = grouped.style
            # Get all unique columns from both L1 and L2 ranges
            all_cols = set(grouped_ranges_by_sample["L1"].keys()).union(set(grouped_ranges_by_sample["L2"].keys()))

            def apply_highlight(row):
                styles = []
                range_key = get_range_key_for_row(row)
                ranges = grouped_ranges_by_sample.get(range_key, grouped_ranges_by_sample["L1"])
                for col in grouped.columns:
                    if col in ranges and col != "Sample Type": # Exclude 'Sample Type' column from highlighting
                        low, high = ranges[col]
                        try:
                            v = float(row[col])
                            v_rounded = round(v, 1) # Round the value here as well for consistency
                            if v_rounded < low or v_rounded > high:
                                styles.append("color: red")
                            else:
                                styles.append("")
                        except Exception:
                            styles.append("")
                    else:
                        styles.append("") # No highlighting for columns not in ranges or 'Sample Type'
                return styles

            styled = grouped.style.apply(apply_highlight, axis=1)
            return styled


        # Show preview before export with highlighting
        st.write("Preview Cleaned Data:")
        # Apply highlighting to the 'grouped' DataFrame        
        grouped.index = grouped.index + 1  # Start index from 1 for display
        st.dataframe(highlight_grouped_dataframe(grouped))

        # Convert to CSV for download
        csv = grouped.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Cleaned CSV",
            data=csv,
            file_name="TEG_grouped.csv",
            mime="text/csv"

        )


