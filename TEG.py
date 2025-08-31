import streamlit as st
import pandas as pd

st.title("TEG Data Viewer")

uploaded_file = st.file_uploader("Upload a TEG CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Preview of Data:", df.head())

    # Filter by date
    if "Date/Time Run" in df.columns:
        df["Date/Time Run"] = pd.to_datetime(df["Date/Time Run"], errors="coerce")
        start_date, end_date = st.date_input(
            "Select Date Range",
            [df["Date/Time Run"].min(), df["Date/Time Run"].max()]
        )
        filtered = df[(df["Date/Time Run"] >= pd.Timestamp(start_date)) &
                      (df["Date/Time Run"] <= pd.Timestamp(end_date))]
        st.write("Filtered Data", filtered)

    # Basic summary stats
    st.write("Summary of Results:", df[["R (min)", "MA (mm)", "LY30 (%)"]].describe())
