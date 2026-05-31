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
ADDITIONAL_XY_DATA_PATH = REPO_ROOT / "data" / "additional_narratives_xy.csv"

LOCATION_COORDINATES = {
    "Tenderloin": (37.7842, -122.4142),
    "Embarcadero": (37.7955, -122.3937),
    "SOMA": (37.7785, -122.4056),
    "Mission District": (37.7599, -122.4148),
    "Financial District": (37.7946, -122.3999),
    "Castro": (37.7609, -122.4350),
}

DATASET_OPTIONS = {
    "Simulated demo data": {
        "preferred_path": XY_DATA_PATH,
        "fallback_path": RAW_DATA_PATH,
        "note": "Synthetic demonstration data for testing the workflow. Not observed rider evidence.",
    },
    "Additional narratives with XY": {
        "preferred_path": ADDITIONAL_XY_DATA_PATH,
        "fallback_path": None,
        "note": "Curated additional narratives with actual or documented XY coordinates, when available.",
    },
}

REQUIRED_COLUMNS = {"Service", "Scenario", "Location", "Sentiment", "Latitude", "Longitude"}


def geocode_known_locations(df: pd.DataFrame) -> pd.DataFrame:
    """Add approximate coordinates for known SF neighborhoods when lat/lon are missing."""
    records = df.copy()
    if "Latitude" not in records.columns or "Longitude" not in records.columns:
        records["Latitude"] = records["Location"].map(lambda x: LOCATION_COORDINATES.get(str(x), (None, None))[0])
        records["Longitude"] = records["Location"].map(lambda x: LOCATION_COORDINATES.get(str(x), (None, None))[1])
    return records.dropna(subset=["Latitude", "Longitude"])


@st.cache_data
def load_dataset(dataset_label: str) -> tuple[pd.DataFrame, Path, str]:
    """Load the selected dataset and return data, source path, and dataset note."""
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


st.set_page_config(page_title="Rideshare Safety Rider Analysis", layout="wide")

st.title("Rideshare Safety Rider Analysis")
st.caption(
    "Prototype dashboard for exploring rider safety, trust, and comfort scenarios "
    "across autonomous and human-driven ridehail services."
)

with st.sidebar:
    st.header("Dataset")
    selected_dataset = st.selectbox("Choose dataset", list(DATASET_OPTIONS.keys()))

try:
    df, source_path, dataset_note = load_dataset(selected_dataset)
except FileNotFoundError:
    st.warning(
        "The selected dataset is not available yet. Add `data/additional_narratives_xy.csv` "
        "using the schema in `docs/data_dictionary.md`, then redeploy or refresh the app."
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

filtered_df = df[
    df["Service"].isin(selected_services)
    & df["Sentiment"].isin(selected_sentiments)
    & df["Scenario"].isin(selected_scenarios)
]

metric_cols = st.columns(4)
metric_cols[0].metric("Records", len(filtered_df))
metric_cols[1].metric("Services", filtered_df["Service"].nunique())
metric_cols[2].metric("Scenarios", filtered_df["Scenario"].nunique())
if "Sentiment Score" in filtered_df.columns and len(filtered_df) > 0:
    metric_cols[3].metric("Average sentiment", f"{filtered_df['Sentiment Score'].mean():.2f}")
else:
    metric_cols[3].metric("Average sentiment", "N/A")

st.subheader("Scenario geography")
m = folium.Map(location=[37.7749, -122.4194], zoom_start=12, tiles="CartoDB positron")
if len(filtered_df) > 0:
    heat_data = filtered_df[["Latitude", "Longitude"]].values.tolist()
    HeatMap(heat_data, radius=18, blur=20).add_to(m)
    for _, row in filtered_df.iterrows():
        popup = f"{row.get('Service', '')}: {row.get('Scenario', '')} ({row.get('Sentiment', '')})"
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
    st.subheader("Scenario mentions")
    scenario_counts = filtered_df.groupby(["Scenario", "Service"]).size().reset_index(name="Count")
    if len(scenario_counts) > 0:
        fig = px.bar(scenario_counts, x="Scenario", y="Count", color="Service", barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No records match the current filters.")

with chart_cols[1]:
    st.subheader("Sentiment distribution")
    sentiment_counts = filtered_df.groupby(["Sentiment", "Service"]).size().reset_index(name="Count")
    if len(sentiment_counts) > 0:
        fig = px.bar(sentiment_counts, x="Sentiment", y="Count", color="Service", barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No records match the current filters.")

st.subheader("Filtered records")
st.dataframe(filtered_df, use_container_width=True)
