"""
Interactive Dashboard - Video Game Sales Dataset
==================================================
An interactive Streamlit dashboard that lets a user filter the
vgsales dataset (by Genre, Platform, and Year range) and explore several of
the visualizations built in Part C dynamically.

Run locally with:
    streamlit run dashboard_app.py

Deploy for free on Streamlit Community Cloud (share.streamlit.io) by
pushing this file + vgsales.csv to a GitHub repo and pointing Streamlit at it.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# ----------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Video Game Sales Dashboard",
    page_icon="🎮",
    layout="wide",
)


# ----------------------------------------------------------------------
# Responsive tweaks: tighten spacing and shrink KPI text on narrow screens
# (phones / split-screen windows) so nothing gets cramped or clipped.
# ----------------------------------------------------------------------
st.markdown(
    """
    <style>
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] p, [data-testid="stMetricLabel"] p {
        white-space: normal !important;
        overflow-wrap: break-word;
        text-overflow: clip !important;
        line-height: 1.2;
    }
    @media (max-width: 640px) {
        .block-container { padding: 1rem 0.75rem 2rem 0.75rem; }
        [data-testid="stMetricValue"] { font-size: 1.3rem; }
        [data-testid="stMetricLabel"] { font-size: 0.8rem; }
        [data-testid="stMarkdownContainer"] h1 { font-size: 1.6rem !important; }
        [data-testid="stMarkdownContainer"] h3 { font-size: 1.15rem !important; }
    }
    @media (min-width: 641px) and (max-width: 1024px) {
        .block-container { padding: 1.5rem 1.5rem 2rem 1.5rem; }
        [data-testid="stMetricValue"] { font-size: 1.2rem; }
        [data-testid="stMetricLabel"] { font-size: 0.8rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎮 Video Game Sales  Dashboard")
st.caption(
    "Explore the vgsales.csv dataset (16,598 titles, 1980-2020) dynamically. "
    "Use the sidebar filters to narrow down by genre, platform, and release year."
)


# ----------------------------------------------------------------------
# Data loading and light cleaning (mirrors Part B of the analysis notebook)
# ----------------------------------------------------------------------
@st.cache_data
def load_data(path: str = "vgsales.csv") -> pd.DataFrame:
    data = pd.read_csv(path)
    data["Year"] = data["Year"].fillna(data["Year"].median())
    data["Year"] = data["Year"].astype(int)
    data["Publisher"] = data["Publisher"].fillna("Unknown")
    data["Genre"] = data["Genre"].astype(str).str.strip()
    data["Platform"] = data["Platform"].astype(str).str.strip()
    data["Release_Decade"] = (data["Year"] // 10 * 10).astype(str) + "s"
    return data


df = load_data()

# ----------------------------------------------------------------------
# Sidebar - interactive filter controls
# ----------------------------------------------------------------------
st.sidebar.header("Filters")

genre_options = sorted(df["Genre"].unique())
selected_genres = st.sidebar.multiselect(
    "Genre", options=genre_options, default=genre_options
)

platform_options = sorted(df["Platform"].unique())
selected_platforms = st.sidebar.multiselect(
    "Platform", options=platform_options, default=platform_options
)

year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
selected_years = st.sidebar.slider(
    "Release Year range",
    min_value=year_min, max_value=year_max,
    value=(2000, year_max),
)

top_n = st.sidebar.slider("Top-N games / publishers to show", min_value=5, max_value=30, value=10)

metric_options = ["Global_Sales", "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]
selected_metric = st.sidebar.selectbox("Sales metric to analyze", options=metric_options, index=0)

# Apply filters
filtered = df[
    df["Genre"].isin(selected_genres)
    & df["Platform"].isin(selected_platforms)
    & df["Year"].between(selected_years[0], selected_years[1])
]

st.sidebar.markdown(f"**{len(filtered):,}** titles match the current filters "
                     f"(of {len(df):,} total).")

if filtered.empty:
    st.warning("No data matches the current filter selection. Please widen your filters.")
    st.stop()

# ----------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Titles", f"{len(filtered):,}")
kpi2.metric(f"Total {selected_metric.replace('_', ' ')}", f"{filtered[selected_metric].sum():,.1f}M")
kpi3.metric(f"Avg {selected_metric.replace('_', ' ')} / title", f"{filtered[selected_metric].mean():,.2f}M")
kpi4.metric("Best-selling title", filtered.loc[filtered[selected_metric].idxmax(), "Name"])

st.divider()

# ----------------------------------------------------------------------
# Visualization 1: Ranked bar chart - Top N games by selected metric
# ----------------------------------------------------------------------
st.subheader(f"Top {top_n} Games by {selected_metric.replace('_', ' ')}")
top_games = (
    filtered.sort_values(selected_metric, ascending=False)
    .head(top_n)[["Name", "Platform", "Genre", "Year", selected_metric]]
)
fig_top = px.bar(
    top_games.sort_values(selected_metric),
    x=selected_metric, y="Name", color="Genre", orientation="h",
    hover_data=["Platform", "Year"],
    labels={selected_metric: f"{selected_metric.replace('_', ' ')} (millions)", "Name": "Game"},
)
fig_top.update_layout(height=max(350, 32 * top_n), margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig_top, use_container_width=True, config={"responsive": True})

# ----------------------------------------------------------------------
# Visualization 2: Sales trend over time
# ----------------------------------------------------------------------
st.subheader(f"{selected_metric.replace('_', ' ')} Trend Over Time")
yearly = filtered.groupby("Year")[selected_metric].sum().reset_index()
fig_trend = px.line(
    yearly, x="Year", y=selected_metric, markers=True,
    labels={selected_metric: f"Total {selected_metric.replace('_', ' ')} (millions)"},
)
fig_trend.update_layout(margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig_trend, use_container_width=True, config={"responsive": True})

# ----------------------------------------------------------------------
# Visualization 3: Genre x Platform treemap
# ----------------------------------------------------------------------
st.subheader("Sales Breakdown by Genre and Platform")
tree_data = (
    filtered.groupby(["Genre", "Platform"])[selected_metric].sum().reset_index()
)
tree_data = tree_data[tree_data[selected_metric] > 0]
fig_tree = px.treemap(
    tree_data, path=["Genre", "Platform"], values=selected_metric,
    color=selected_metric, color_continuous_scale="Blues",
)
tree_row_count = tree_data["Genre"].nunique()
fig_tree.update_layout(height=max(400, 40 * tree_row_count), margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig_tree, use_container_width=True, config={"responsive": True})

# ----------------------------------------------------------------------
# Visualization 4: Regional sales comparison scatter
# ----------------------------------------------------------------------
st.subheader("Regional Sales Comparison")
col_a, col_b = st.columns([2, 1])
with col_b:
    x_axis = st.selectbox("X-axis region", metric_options, index=1)
    y_axis = st.selectbox("Y-axis region", metric_options, index=0)
with col_a:
    fig_scatter = px.scatter(
        filtered.sample(n=min(2000, len(filtered)), random_state=42),
        x=x_axis, y=y_axis, color="Genre", size="Global_Sales",
        hover_data=["Name", "Platform", "Year"],
        labels={x_axis: f"{x_axis.replace('_', ' ')} (millions)",
                y_axis: f"{y_axis.replace('_', ' ')} (millions)"},
    )
    fig_scatter.update_layout(margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True, config={"responsive": True})

# ----------------------------------------------------------------------
# Data table (expandable)
# ----------------------------------------------------------------------
with st.expander("View filtered raw data"):
    st.dataframe(filtered.reset_index(drop=True))

st.caption(
    "Dashboard functionality: sidebar controls (Genre / Platform multiselects, Year-range slider, "
    "Top-N slider, and sales-metric dropdown) dynamically filter and re-render all four charts "
    "above — a ranked top-titles bar chart, a yearly sales trend line, a Genre-Platform treemap, "
    "and a configurable regional sales scatter plot."
)
