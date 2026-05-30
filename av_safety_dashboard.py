
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap
import plotly.express as px

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("sentiment_data_sample.csv")

df = load_data()

# Sidebar filters
st.sidebar.title("Filter Options")
service_filter = st.sidebar.multiselect("Select Service", options=df["Service"].unique(), default=df["Service"].unique())
sentiment_filter = st.sidebar.multiselect("Select Sentiment", options=df["Sentiment"].unique(), default=df["Sentiment"].unique())

filtered_df = df[(df["Service"].isin(service_filter)) & (df["Sentiment"].isin(sentiment_filter))]

# Title
st.title("Waymo vs. Uber: Trust & Safety Sentiment Mapping")

# Map Display
st.subheader("Sentiment Heatmap (San Francisco)")
m = folium.Map(location=[37.7749, -122.4194], zoom_start=13)
HeatMap(filtered_df[["Latitude", "Longitude"]].values.tolist(), radius=10).add_to(m)
folium_static(m)

# Sentiment Distribution
st.subheader("Sentiment Distribution")
sentiment_counts = filtered_df.groupby(["Service", "Sentiment"]).size().reset_index(name="Count")
fig = px.bar(sentiment_counts, x="Sentiment", y="Count", color="Service", barmode="group")
st.plotly_chart(fig)

# Display sample data
st.subheader("Sample Sentiment Data")
st.dataframe(filtered_df.head(10))
