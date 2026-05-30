from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import folium_static


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = REPO_ROOT / "data" / "simulated_sentiment_scenario_data.csv"
ROOT_DATA_FALLBACK = REPO_ROOT / "simulated_sentiment_scenario_data.csv"

LOCATION_COORDINATES = {
    "Tenderloin": (37.7842, -122.4142),
    "Embarcadero": (37.7955, -122.3937),
    "SOMA": (37.7785, -122.4056),
    "Mission District": (37.7599, -122.4148),
    "Financial District": (37.7946, -122.3999),
    "Castro": (37.7609, -122.4350),
}


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load the simulated scenario dataset and add coordinates when needed."""
    path = DATA_PATH if DATA_PATH.exists() else ROOT_DATA_FALLBACK
    if not path.exists():
        st.error(
            "Could not find simulated_sentiment_scenario_data.csv. "
            "Place it in the data/ directory."
        )
        st.stop()

    df = pd.read_csv(path)
    df.columns = [col.strip() for col in df.columns]

    if "Latitude" not in df.columns or "Longitude" not in df.columns:
        df["Latitude"] = df["Location"].map(lambda x: LOCATION_COORDINATES.get(str(x), (None, None))[0])
        df["Longitude"] = df["Location"].map(lambda x: LOCATION_COORDINATES.get(str(x), (None, None))[1])

    df = df.dropna(subset=["Latitude", "Longitude"])
    return df


st.set_page_config(page_title="Rideshare Safety Rider Analysis", layout="wide")

st.title("Rideshare Safety Rider Analysis")
st.caption(
    "Prototype dashboard for exploring simulated rider safety, trust, and comfort scenarios "
    "across autonomous and human-driven ridehail services."
)

with st.expander("Important data note", expanded=True):
    st.write(
        "This dashboard currently uses simulated data. It is intended to demonstrate a "
        "workflow for scenario tagging, sentiment comparison, and geospatial visualization. "
        "It should not be interpreted as observed rider behavior or verified incident evidence."
    )

df = load_data()

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
map_center = [37.7749, -122.4194]
m = folium.Map(location=map_center, zoom_start=12, tiles="CartoDB positron")
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
