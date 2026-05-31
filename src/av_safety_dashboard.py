from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import folium_static


REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = REPO_ROOT / "data" / "simulated_sentiment_scenario_data.csv"
XY_DATA_PATH = REPO_ROOT / "data" / "simulated_sentiment_scenario_data_xy.csv"
PUBLIC_NARRATIVES_PATH = REPO_ROOT / "data" / "public_narratives_xy.csv"
RESEARCH_RIDER_PATH = REPO_ROOT / "data" / "research_rider_dataset.csv"

LOCATION_COORDINATES = {
    "Tenderloin": (37.7842, -122.4142),
    "Embarcadero": (37.7955, -122.3937),
    "SOMA": (37.7785, -122.4056),
    "Mission District": (37.7599, -122.4148),
    "Financial District": (37.7946, -122.3999),
    "Castro": (37.7609, -122.4350),
}

DATASET_OPTIONS = {
    "Simulated Scenario Dataset": {
        "preferred_path": XY_DATA_PATH,
        "fallback_path": RAW_DATA_PATH,
        "note": "Synthetic demonstration data for testing the workflow. Not observed rider evidence.",
    },
    "Research Rider Dataset": {
        "preferred_path": RESEARCH_RIDER_PATH,
        "fallback_path": None,
        "note": "Public-safe derived rider/non-rider survey dataset. Raw open-ended responses are omitted; riders use dropoff coordinates and non-riders use survey-location coordinates.",
    },
    "Public Narrative Dataset": {
        "preferred_path": PUBLIC_NARRATIVES_PATH,
        "fallback_path": None,
        "note": "Curated public narratives with documented XY coordinates, when available.",
    },
}

REQUIRED_COLUMNS = {"Service", "Scenario", "Location", "Sentiment", "Latitude", "Longitude"}


def geocode_known_locations(df: pd.DataFrame) -> pd.DataFrame:
    records = df.copy()
    if "Latitude" not in records.columns or "Longitude" not in records.columns:
        records["Latitude"] = records["Location"].map(lambda x: LOCATION_COORDINATES.get(str(x), (None, None))[0])
        records["Longitude"] = records["Location"].map(lambda x: LOCATION_COORDINATES.get(str(x), (None, None))[1])
    return records.dropna(subset=["Latitude", "Longitude"])


@st.cache_data
def load_dataset(dataset_label: str) -> tuple[pd.DataFrame, Path, str]:
    config = DATASET_OPTIONS[dataset_label]
    preferred_path = config["preferred_path"]
    fallback_path = config["fallback_path"]

    if preferred_path.exists():
        path = preferred_path
    elif fallback_path is not None and fallback_path.exists():
        path = fallback_path
    else:
        raise FileNotFoundError(str(preferred_path))

    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]
    df = geocode_known_locations(df)
    return df, path, config["note"]


def top_count_chart(data: pd.DataFrame, column: str, title: str, color: str | None = None):
    if column not in data.columns:
        st.info(f"Column `{column}` is not available for this dataset.")
        return
    chart_data = data.groupby([column] + ([color] if color and color in data.columns else [])).size().reset_index(name="Count")
    if chart_data.empty:
        st.info("No records match the current filters.")
        return
    fig = px.bar(chart_data, x=column, y="Count", color=color if color in chart_data.columns else None, barmode="group")
    fig.update_layout(title=title, xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)


def mean_value_chart(data: pd.DataFrame):
    value_cols = [
        "Zero_Emission_Score",
        "Accessibility_Score",
        "Distribution_Score",
        "Transit_Connectivity_Score",
    ]
    available = [col for col in value_cols if col in data.columns]
    if not available:
        return
    rows = []
    for col in available:
        rows.append({"Value": col.replace("_Score", "").replace("_", " "), "Average score": pd.to_numeric(data[col], errors="coerce").mean()})
    value_df = pd.DataFrame(rows).dropna()
    if not value_df.empty:
        fig = px.bar(value_df, x="Value", y="Average score")
        fig.update_layout(title="Average value importance scores", xaxis_tickangle=-30, yaxis_range=[0, 5])
        st.plotly_chart(fig, use_container_width=True)


st.set_page_config(page_title="Rideshare Safety Rider Analysis", layout="wide")

st.title("Rideshare Safety Rider Analysis")
st.caption("Prototype dashboard for exploring rider safety, trust, comfort, and service design across autonomous and human-driven ridehail services.")

with st.sidebar:
    st.header("Dataset")
    selected_dataset = st.selectbox("Choose dataset", list(DATASET_OPTIONS.keys()))

try:
    df, source_path, dataset_note = load_dataset(selected_dataset)
except FileNotFoundError:
    st.warning(
        f"The selected dataset is not available yet. Expected `{DATASET_OPTIONS[selected_dataset]['preferred_path'].relative_to(REPO_ROOT)}`."
    )
    st.stop()

missing_columns = REQUIRED_COLUMNS - set(df.columns)
if missing_columns:
    st.error(f"The selected dataset is missing required columns: {sorted(missing_columns)}")
    st.stop()

with st.expander("Important data note", expanded=True):
    st.write(dataset_note)
    st.write(f"Loaded dataset: `{source_path.relative_to(REPO_ROOT)}`")

with st.sidebar:
    st.header("Filters")
    service_options = sorted(df["Service"].dropna().unique())
    sentiment_options = sorted(df["Sentiment"].dropna().unique())
    scenario_options = sorted(df["Scenario"].dropna().unique())

    selected_services = st.multiselect("Service", service_options, default=service_options)
    selected_sentiments = st.multiselect("Sentiment", sentiment_options, default=sentiment_options)
    selected_scenarios = st.multiselect("Scenario", scenario_options, default=scenario_options)

    if "Respondent_Group" in df.columns:
        respondent_options = sorted(df["Respondent_Group"].dropna().unique())
        selected_respondents = st.multiselect("Respondent group", respondent_options, default=respondent_options)
    else:
        selected_respondents = None

filtered_df = df[
    df["Service"].isin(selected_services)
    & df["Sentiment"].isin(selected_sentiments)
    & df["Scenario"].isin(selected_scenarios)
]

if selected_respondents is not None:
    filtered_df = filtered_df[filtered_df["Respondent_Group"].isin(selected_respondents)]

metric_cols = st.columns(5)
metric_cols[0].metric("Records", len(filtered_df))
metric_cols[1].metric("Services", filtered_df["Service"].nunique())
metric_cols[2].metric("Scenarios", filtered_df["Scenario"].nunique())
if "Respondent_Group" in filtered_df.columns:
    metric_cols[3].metric("Riders", int((filtered_df["Respondent_Group"] == "Rider").sum()))
    metric_cols[4].metric("Non-riders", int((filtered_df["Respondent_Group"] == "Non-rider").sum()))
else:
    metric_cols[3].metric("Locations", filtered_df["Location"].nunique())
    if "Sentiment Score" in filtered_df.columns and len(filtered_df) > 0:
        metric_cols[4].metric("Avg sentiment", f"{filtered_df['Sentiment Score'].mean():.2f}")
    else:
        metric_cols[4].metric("Avg sentiment", "N/A")

st.subheader("Scenario geography")
m = folium.Map(location=[37.7749, -122.4194], zoom_start=12, tiles="CartoDB positron")
if len(filtered_df) > 0:
    HeatMap(filtered_df[["Latitude", "Longitude"]].values.tolist(), radius=18, blur=20).add_to(m)
    for _, row in filtered_df.iterrows():
        group = row.get("Respondent_Group", row.get("Service", ""))
        popup = f"{group}: {row.get('Scenario', '')} ({row.get('Sentiment', '')})"
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=4,
            fill=True,
            fill_opacity=0.6,
            popup=popup,
        ).add_to(m)
folium_static(m, width=1100, height=500)

chart_cols = st.columns(2)
with chart_cols[0]:
    top_count_chart(filtered_df, "Scenario", "Scenario mentions", "Respondent_Group" if "Respondent_Group" in filtered_df.columns else "Service")
with chart_cols[1]:
    top_count_chart(filtered_df, "Sentiment", "Sentiment distribution", "Respondent_Group" if "Respondent_Group" in filtered_df.columns else "Service")

if selected_dataset == "Research Rider Dataset":
    st.subheader("Research rider survey views")
    survey_cols = st.columns(2)
    with survey_cols[0]:
        top_count_chart(filtered_df, "Trip_Purpose", "Trip purpose", "Respondent_Group")
        top_count_chart(filtered_df, "Late_Night_Travel_Change", "Late-night travel change", "Respondent_Group")
    with survey_cols[1]:
        top_count_chart(filtered_df, "Alternative_Mode", "Alternative mode", "Respondent_Group")
        top_count_chart(filtered_df, "Views_Changed", "Views changed after participation", "Respondent_Group")
    mean_value_chart(filtered_df)

st.subheader("Filtered records")
st.dataframe(filtered_df, use_container_width=True)
