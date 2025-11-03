"""
Streamlit app: Active Genocides – World Map
-------------------------------------------
This app renders a world map of ongoing/active genocides / atrocity risks from a CSV you maintain.

⚠️ Sensitive topic: Please cite reputable sources and keep the dataset updated. The app only visualizes
what your CSV provides; it does not make determinations.

Quick start
-----------
1) (Recommended) Use a fresh env to avoid binary conflicts (conda or venv).
2) Install deps (versions known to work together):
   pip install "streamlit==1.39.0" "pandas==2.2.2" "numpy==1.26.4" "pydeck==0.9.1"
3) Run the app:
   streamlit run app.py
4) Put your CSV at ./data/genocides.csv (preferred) or ./genocides.csv

CSV schema (required columns)
-----------------------------
- id (str)                        — unique identifier
- name (str)                      — short case name
- country (str)
- region (str)                    — e.g., Africa, Asia, Europe, Americas, Oceania, MENA
- latitude (float)
- longitude (float)
- start_date (YYYY-MM-DD)
- status (str)                    — e.g., "ongoing", "escalating", "at-risk"
- perpetrators (str)
- targeted_group (str)
- est_deaths (int or blank)
- last_verified (YYYY-MM-DD)
- sources (semicolon-separated URLs)
- summary (str)

If no CSV exists, use the sidebar button to create a sample file.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List
from datetime import datetime

import pandas as pd
import streamlit as st
import pydeck as pdk

# -----------------------------
# Config & constants
# -----------------------------
REQUIRED_COLS: List[str] = [
    "id",
    "name",
    "country",
    "region",
    "latitude",
    "longitude",
    "start_date",
    "status",
    "perpetrators",
    "targeted_group",
    "est_deaths",
    "last_verified",
    "sources",
    "summary",
]
PREFERRED_PATH = Path("../data/genocides.csv")
FALLBACK_PATH = Path("genocides.csv")

st.set_page_config(
    page_title="Active Genocides – World Map",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Active Genocides – World Map")
st.caption(
    "This map visualizes cases from your CSV. Hover markers for details; view sources per case below."
)

# -----------------------------
# Utilities
# -----------------------------

def _coerce_date(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.date


@st.cache_data(show_spinner=False)
def load_csv() -> pd.DataFrame | None:
    path = PREFERRED_PATH if PREFERRED_PATH.exists() else (FALLBACK_PATH if FALLBACK_PATH.exists() else None)
    if path is None:
        return None

    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        st.error(f"Missing required columns in {path}: {missing}")
        return pd.DataFrame()

    # Type cleaning
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["est_deaths"] = pd.to_numeric(df["est_deaths"], errors="coerce")
    df["start_date"] = _coerce_date(df["start_date"])  # may become NaT -> NaN
    df["last_verified"] = _coerce_date(df["last_verified"])  # may become NaT -> NaN

    # Basic row validation hints
    problems = []
    for idx, row in df.iterrows():
        msgs = []
        try:
            lat = float(row["latitude"]) if pd.notna(row["latitude"]) else None
            lon = float(row["longitude"]) if pd.notna(row["longitude"]) else None
        except Exception:
            lat, lon = None, None
        if lat is None or lon is None:
            msgs.append("lat/lon missing or invalid")
        else:
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                msgs.append("lat/lon out of range")
        if not str(row.get("sources", "")).strip():
            msgs.append("missing sources")
        if msgs:
            problems.append((idx, "; ".join(msgs)))
    if problems:
        with st.expander("⚠️ Data quality issues (click to expand)"):
            for i, msg in problems:
                st.write(f"Row {i}: {msg}")

    return df


def write_sample_csv(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    sample = pd.DataFrame([
        {
            "id": "EX-001",
            "name": "Example Case",
            "country": "Exampleland",
            "region": "Example Region",
            "latitude": 34.0,
            "longitude": 71.5,
            "start_date": "2024-01-01",
            "status": "ongoing",
            "perpetrators": "Example Security Forces",
            "targeted_group": "Example Minority",
            "est_deaths": 1200,
            "last_verified": "2025-11-01",
            "sources": "https://example.org/report; https://another.org/article",
            "summary": "Short placeholder summary describing the situation and citing sources.",
        },
        {
            "id": "EX-002",
            "name": "Escalating Violence",
            "country": "Samplestan",
            "region": "Asia",
            "latitude": 35.7,
            "longitude": 51.3,
            "start_date": "2025-04-20",
            "status": "escalating",
            "perpetrators": "Paramilitary Group X",
            "targeted_group": "Group Y",
            "est_deaths": "",
            "last_verified": "2025-10-15",
            "sources": "https://ngo.example/briefing",
            "summary": "Risks increasing; monitor closely.",
        },
    ])
    sample.to_csv(path, index=False)


# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.header("Data source")
    st.write("Place your CSV at **data/genocides.csv** (preferred) or **./genocides.csv**.")

    if not PREFERRED_PATH.exists() and not FALLBACK_PATH.exists():
        if st.button("Create sample CSV at ./data/genocides.csv"):
            write_sample_csv(PREFERRED_PATH)
            st.success(f"Sample written to {PREFERRED_PATH}")
            st.cache_data.clear()

    st.divider()
    st.header("Map filters")

# Load data after potential sample creation
_df = load_csv()

if _df is None:
    st.info("No CSV found yet. Use the sidebar to create a sample, or add your own CSV and rerun.")
    st.stop()

if _df.empty:
    st.warning("CSV loaded but contains issues. See above for details.")

# Build dynamic filters
regions = sorted([r for r in _df["region"].dropna().astype(str).unique() if r])
statuses = sorted([s for s in _df["status"].dropna().astype(str).unique() if s])

with st.sidebar:
    sel_regions = st.multiselect("Region", options=regions, default=regions)
    sel_status = st.multiselect("Status", options=statuses, default=statuses)
    yr_min = int(pd.to_datetime(_df["start_date"], errors="coerce").dt.year.min()) if not _df.empty else 1900
    yr_max = int(pd.to_datetime(_df["start_date"], errors="coerce").dt.year.max()) if not _df.empty else datetime.now().year
    year_range = st.slider(
        "Start year range",
        min_value=max(1900, yr_min),
        max_value=max(yr_max, yr_min),
        value=(max(1900, yr_min), max(yr_max, yr_min)),
    )
    show_labels = st.checkbox("Show text labels on map", value=False)

# Apply filters
fdf = _df.copy()
if sel_regions:
    fdf = fdf[fdf["region"].astype(str).isin(sel_regions)]
if sel_status:
    fdf = fdf[fdf["status"].astype(str).isin(sel_status)]

sd = pd.to_datetime(fdf["start_date"], errors="coerce")
mask_year = (sd.dt.year >= year_range[0]) & (sd.dt.year <= year_range[1])
fdf = fdf[mask_year]

# Default view state
if not fdf.empty:
    mean_lat = float(fdf["latitude"].astype(float).mean())
    mean_lon = float(fdf["longitude"].astype(float).mean())
else:
    mean_lat, mean_lon = 20.0, 0.0

view_state = pdk.ViewState(latitude=mean_lat, longitude=mean_lon, zoom=1.5, bearing=0, pitch=0)

# Color by status
STATUS_COLOR = {
    "ongoing": [220, 20, 60],      # crimson
    "escalating": [255, 140, 0],   # dark orange
    "at-risk": [255, 215, 0],      # gold
}

default_color = [100, 149, 237]  # cornflower blue
fdf = fdf.assign(
    color=fdf["status"].str.lower().map(lambda s: STATUS_COLOR.get(s, default_color))
)

# Tooltip (stringified; safe for JSON)
fdf = fdf.assign(
    tooltip=(
        "<b>" + fdf["name"].astype(str) + "</b><br>" +
        fdf["country"].astype(str) + " — " + fdf["region"].astype(str) + "<br>" +
        "Status: " + fdf["status"].astype(str) + "<br>" +
        "Targeted: " + fdf["targeted_group"].astype(str) + "<br>" +
        "Perpetrators: " + fdf["perpetrators"].astype(str) + "<br>" +
        "Since: " + fdf["start_date"].astype(str) + "<br>" +
        "Last verified: " + fdf["last_verified"].astype(str)
    )
)

# Minimal map dataframe (avoid non-serializable types)
map_cols = ["longitude", "latitude", "color", "tooltip", "name"]
df_map = fdf[map_cols].copy()
df_map["longitude"] = pd.to_numeric(df_map["longitude"], errors="coerce")
df_map["latitude"] = pd.to_numeric(df_map["latitude"], errors="coerce")
df_map = df_map.dropna(subset=["longitude", "latitude"])  # drop invalid points

# Map layers
scatter = pdk.Layer(
    "ScatterplotLayer",
    data=df_map,
    get_position="[longitude, latitude]",
    get_fill_color="color",
    get_radius=200000,
    pickable=True,
    auto_highlight=True,
)

layers = [scatter]

if show_labels and not df_map.empty:
    labels = pdk.Layer(
        "TextLayer",
        data=df_map,
        get_position="[longitude, latitude]",
        get_text="name",
        get_size=16,
        get_color=[0, 0, 0],
        get_angle=0,
        get_alignment_baseline="bottom",
    )
    layers.append(labels)

# Mapbox token (optional). If missing, fall back to OpenStreetMap TileLayer
# Avoid touching st.secrets when no secrets.toml exists (prevents StreamlitSecretNotFoundError)
MAPBOX_TOKEN = os.getenv('MAPBOX_API_KEY', '')
try:
    from pathlib import Path
    if Path.home().joinpath('.streamlit', 'secrets.toml').exists() or Path('.streamlit/secrets.toml').exists():
        # Only read st.secrets if a secrets file exists
        try:
            MAPBOX_TOKEN = st.secrets.get('MAPBOX_API_KEY', MAPBOX_TOKEN)
        except Exception:
            pass
except Exception:
    pass

base_layers = []
if MAPBOX_TOKEN:
    pdk.settings.mapbox_api_key = MAPBOX_TOKEN
    map_style = 'mapbox://styles/mapbox/light-v10'
else:
    map_style = None
    base_layers.append(
        pdk.Layer(
            'TileLayer',
            data='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            min_zoom=0,
            max_zoom=19,
            tile_size=256,
        )
    )

all_layers = base_layers + layers

r = pdk.Deck(
    map_style=map_style,
    initial_view_state=view_state,
    layers=all_layers,
    tooltip={'html': '{tooltip}', 'style': {'backgroundColor': 'white', 'color': 'black'}},
)

st.pydeck_chart(r, use_container_width=True)

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Cases")
    display_cols = [
        "id", "name", "country", "region", "status", "targeted_group", "perpetrators", "start_date", "last_verified", "est_deaths"
    ]

    # Try pyarrow-backed dataframe; fall back to HTML table if pyarrow/numpy mismatch occurs
    try:
        import pyarrow  # noqa: F401
        st.dataframe(fdf[display_cols].sort_values(["region", "country", "name"]))
    except Exception as e:
        msg = str(e).split("\n")[0]
        st.warning(f"PyArrow not available/compatible ({msg}). Falling back to HTML table rendering.")
        html_table = fdf[display_cols].sort_values(["region", "country", "name"]).to_html(index=False)
        st.markdown(html_table, unsafe_allow_html=True)

with col2:
    st.subheader("Download / Meta")
    st.download_button(
        label="Download filtered CSV",
        data=fdf.to_csv(index=False).encode("utf-8"),
        file_name="genocides_filtered.csv",
        mime="text/csv",
    )
    st.caption("Filtered rows only. Keep your master CSV under version control for auditability.")

st.divider()

# Sources panel
st.subheader("Sources for filtered cases")
if fdf.empty:
    st.info("No cases match the current filters.")
else:
    for _, row in fdf.iterrows():
        with st.expander(f"{row['name']} — Sources"):
            for raw in str(row.get("sources", "")).split(";"):
                url = raw.strip()
                if not url:
                    continue
                label = url.replace("https://", "").replace("http://", "")
                st.markdown(f"- [{label}]({url})")
            if str(row.get("summary", "")).strip():
                st.write(row.get("summary", ""))

st.caption(
    "Note: This app displays entries from your CSV and the sources you provide. It is not a legal or scholarly determination."
)
