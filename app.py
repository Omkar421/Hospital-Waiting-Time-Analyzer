import io
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="Hospital Waiting Time Analyzer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent
DEFAULT_DATA = ROOT / "hospital_waiting_data.csv"

REQUIRED_COLUMNS = [
    "Patient_ID", "Department", "Arrival_Time",
    "Consultation_Start", "Day"
]
DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

st.markdown("""
<style>
    .main {background-color: #f7f9fc;}
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #e5eaf2; padding: 14px;
        border-radius: 14px;
    }
    .hero {
        padding: 1.3rem 1.5rem; border-radius: 18px;
        background: linear-gradient(120deg, #123b63, #2879a8);
        color: white; margin-bottom: 1rem;
    }
    .hero h1 {color: white; margin: 0;}
    .hero p {color: #e8f4ff; margin: .35rem 0 0 0;}
    .small-note {color: #64748b; font-size: .88rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🏥 Hospital Waiting Time Analyzer</h1>
  <p>Explore patient waiting times, compare departments, and identify busy periods.</p>
</div>
""", unsafe_allow_html=True)

def parse_clock(value):
    """Convert a time value to minutes after midnight."""
    if pd.isna(value):
        return None
    try:
        t = pd.to_datetime(str(value).strip(), format="%H:%M", errors="coerce")
        if pd.isna(t):
            t = pd.to_datetime(str(value).strip(), errors="coerce")
        if pd.isna(t):
            return None
        return int(t.hour * 60 + t.minute)
    except Exception:
        return None

def prepare_data(raw):
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    for col in ["Patient_ID", "Department", "Arrival_Time", "Consultation_Start", "Day"]:
        df[col] = df[col].astype("string").str.strip()

    df["Arrival_Minutes"] = df["Arrival_Time"].map(parse_clock)
    df["Consultation_Minutes"] = df["Consultation_Start"].map(parse_clock)
    df["Waiting_Minutes"] = df["Consultation_Minutes"] - df["Arrival_Minutes"]

    # Correct for a consultation after midnight when the arrival was late at night.
    overnight = df["Waiting_Minutes"] < 0
    df.loc[overnight, "Waiting_Minutes"] = df.loc[overnight, "Waiting_Minutes"] + 1440

    df["Waiting_Minutes"] = pd.to_numeric(df["Waiting_Minutes"], errors="coerce")
    df["Day"] = df["Day"].str.title()
    df["Department"] = df["Department"].fillna("Unknown")
    df["Patient_ID"] = df["Patient_ID"].fillna("Unknown")

    valid = (
        df["Arrival_Minutes"].notna()
        & df["Consultation_Minutes"].notna()
        & df["Waiting_Minutes"].notna()
        & (df["Waiting_Minutes"] >= 0)
        & (df["Waiting_Minutes"] <= 1440)
    )
    cleaned = df.loc[valid].copy()
    return cleaned, len(df) - len(cleaned)

def fmt_minutes(value):
    if pd.isna(value):
        return "—"
    return f"{value:.1f} min"

with st.sidebar:
    st.header("⚙️ Controls")
    st.write("Use the sample dataset or upload your own CSV file.")
    uploaded = st.file_uploader("Upload hospital CSV", type=["csv"])
    st.caption("Expected columns: Patient_ID, Department, Arrival_Time, Consultation_Start, Day")
    st.divider()
    st.subheader("Waiting-time categories")
    st.write("🟢 Short: under 15 minutes")
    st.write("🟡 Moderate: 15–30 minutes")
    st.write("🔴 Long: over 30 minutes")
    st.caption("These are illustrative thresholds for this student project, not clinical standards.")

try:
    if uploaded is not None:
        raw_data = pd.read_csv(uploaded)
        source_name = uploaded.name
    else:
        raw_data = pd.read_csv(DEFAULT_DATA)
        source_name = "Sample dataset"
    data, rejected_count = prepare_data(raw_data)
except Exception as exc:
    st.error(f"Could not read the dataset: {exc}")
    st.info("Please upload a CSV with the five required columns shown in the sidebar.")
    st.stop()

if data.empty:
    st.warning("No valid records were found. Check your time values and required columns.")
    st.stop()

st.caption(f"Data source: **{source_name}** · Valid records: **{len(data)}** · Invalid records skipped: **{rejected_count}**")

with st.sidebar:
    departments = sorted(data["Department"].dropna().unique().tolist())
    chosen_departments = st.multiselect("Departments", departments, default=departments)
    days_available = [d for d in DAY_ORDER if d in data["Day"].unique()]
    days_available += sorted([d for d in data["Day"].unique() if d not in DAY_ORDER])
    chosen_days = st.multiselect("Days", days_available, default=days_available)
    min_wait, max_wait = int(data["Waiting_Minutes"].min()), int(data["Waiting_Minutes"].max())
    if min_wait < max_wait:
        wait_range = st.slider(
            "Waiting time range (minutes)",
            min_value=min_wait,
            max_value=max_wait,
            value=(min_wait, max_wait),
        )
    else:
        wait_range = (min_wait, max_wait)

filtered = data[
    data["Department"].isin(chosen_departments)
    & data["Day"].isin(chosen_days)
    & data["Waiting_Minutes"].between(wait_range[0], wait_range[1])
].copy()

if filtered.empty:
    st.warning("No records match these filters. Change the selections in the sidebar.")
    st.stop()

avg_wait = filtered["Waiting_Minutes"].mean()
median_wait = filtered["Waiting_Minutes"].median()
long_wait_share = (filtered["Waiting_Minutes"] > 30).mean() * 100
top_department = (
    filtered.groupby("Department")["Waiting_Minutes"].mean().sort_values(ascending=False)
)
slowest_department = top_department.index[0] if len(top_department) else "—"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Patients analyzed", f"{len(filtered):,}")
c2.metric("Average wait", fmt_minutes(avg_wait))
c3.metric("Median wait", fmt_minutes(median_wait))
c4.metric("Waits over 30 min", f"{long_wait_share:.1f}%")

st.subheader("📊 Waiting-time overview")
left, right = st.columns(2)

with left:
    dept_summary = (
        filtered.groupby("Department", as_index=False)
        .agg(Average_Wait=("Waiting_Minutes", "mean"), Patients=("Patient_ID", "count"))
        .sort_values("Average_Wait", ascending=False)
    )
    fig = px.bar(
        dept_summary, x="Department", y="Average_Wait", color="Average_Wait",
        hover_data=["Patients"], title="Average waiting time by department",
        labels={"Average_Wait": "Average wait (minutes)", "Department": "Department"},
        color_continuous_scale="Blues",
    )
    fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Minutes")
    st.plotly_chart(fig, use_container_width=True)

with right:
    day_summary = (
        filtered.groupby("Day", as_index=False)
        .agg(Average_Wait=("Waiting_Minutes", "mean"), Patients=("Patient_ID", "count"))
    )
    day_summary["Day"] = pd.Categorical(day_summary["Day"], categories=DAY_ORDER, ordered=True)
    day_summary = day_summary.sort_values("Day")
    fig = px.line(
        day_summary, x="Day", y="Average_Wait", markers=True,
        title="Average waiting time by day",
        labels={"Average_Wait": "Average wait (minutes)", "Day": "Day"},
    )
    fig.update_layout(xaxis_title="", yaxis_title="Minutes")
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    fig = px.histogram(
        filtered, x="Waiting_Minutes", nbins=12,
        title="Distribution of patient waiting times",
        labels={"Waiting_Minutes": "Waiting time (minutes)"},
        color_discrete_sequence=["#2879a8"],
    )
    fig.update_layout(xaxis_title="Minutes", yaxis_title="Number of patients")
    st.plotly_chart(fig, use_container_width=True)

with right:
    hour_data = filtered.copy()
    hour_data["Arrival_Hour"] = (hour_data["Arrival_Minutes"] // 60).astype(int).map(
        lambda h: f"{h:02d}:00"
    )
    hour_summary = (
        hour_data.groupby("Arrival_Hour", as_index=False)
        .agg(Average_Wait=("Waiting_Minutes", "mean"), Patients=("Patient_ID", "count"))
        .sort_values("Arrival_Hour")
    )
    fig = px.bar(
        hour_summary, x="Arrival_Hour", y="Patients",
        title="Patient arrivals by hour",
        hover_data=["Average_Wait"],
        labels={"Arrival_Hour": "Arrival hour", "Patients": "Number of patients"},
    )
    fig.update_layout(xaxis_title="", yaxis_title="Patients")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("💡 Key findings")
if len(top_department):
    st.write(f"- **Longest average wait:** {slowest_department} ({top_department.iloc[0]:.1f} minutes).")
    busiest_day = filtered["Day"].value_counts().idxmax()
    st.write(f"- **Most represented day in this dataset:** {busiest_day} ({int(filtered['Day'].value_counts().iloc[0])} records).")
    st.write(f"- **Patients waiting over 30 minutes:** {int((filtered['Waiting_Minutes'] > 30).sum())} of {len(filtered)} records.")
st.caption("Findings describe the selected dataset only. They do not establish causes or provide medical advice.")

st.subheader("📋 Patient-level data")
display_cols = ["Patient_ID", "Department", "Arrival_Time", "Consultation_Start", "Day", "Waiting_Minutes"]
display_df = filtered[display_cols].copy()
display_df["Waiting_Minutes"] = display_df["Waiting_Minutes"].round(1)
st.dataframe(display_df, use_container_width=True, hide_index=True)

csv_bytes = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download filtered analysis (CSV)",
    data=csv_bytes,
    file_name="hospital_waiting_time_analysis.csv",
    mime="text/csv",
)

with st.expander("ℹ️ How waiting time is calculated"):
    st.write("Waiting time = consultation start time − patient arrival time. Records with invalid times are skipped. The sample data is fictional and is intended for educational demonstration.")
    st.code("Waiting_Minutes = Consultation_Start - Arrival_Time", language="python")

st.markdown("---")
st.markdown("<p class='small-note'>Hospital Waiting Time Analyzer · Student Big Data Analytics Project · Uses sample or user-provided data.</p>", unsafe_allow_html=True)
