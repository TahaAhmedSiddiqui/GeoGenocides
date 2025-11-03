from __future__ import annotations
from pathlib import Path
import pandas as pd

import streamlit as st
import pydeck as pdk


from src.config import PREFERRED_PATH, FALLBACK_PATH, get_mapbox_token
from src.repository import CSVRepository
from src.services import CaseService
from src.map_builder import MapBuilder
from src.view import View


st.set_page_config(page_title="GeoGenocides", page_icon="🔥", layout="wide")
st.title("🌍 GeoGenocides – a World Map of Genocides")
st.caption("This map shows you all active genocides in the world")


# Sidebar: data info & sample creation
with st.sidebar:
    View.sidebar_data_info(str(PREFERRED_PATH), str(FALLBACK_PATH))
    if not PREFERRED_PATH.exists() and not FALLBACK_PATH.exists():
        if st.button("Create sample CSV at ./data/genocides.csv"):
            import pandas as pd
            PREFERRED_PATH.parent.mkdir(parents=True, exist_ok=True)
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
            sample.to_csv(PREFERRED_PATH, index=False)
            st.success(f"Sample written to {PREFERRED_PATH}")
            st.cache_data.clear()


# Load CSV
db = CSVRepository(PREFERRED_PATH, FALLBACK_PATH)
df = db.load()
if df is None:
    st.info("No CSV found yet. Use the sidebar to create a sample, or add your own CSV and rerun.")
    st.stop()


missing = db.validate(df)
if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()


# Normalize, issues
svc = CaseService()
df = svc.normalize(df)
issues = svc.quality_issues(df)
View.expander_issues(issues)


# Sidebar filters
regions = sorted([r for r in df["region"].dropna().astype(str).unique() if r])
statuses = sorted([s for s in df["status"].dropna().astype(str).unique() if s])
yr_min = int(pd.to_datetime(df["start_date"], errors="coerce").dt.year.min()) if not df.empty else 1900
yr_max = int(pd.to_datetime(df["start_date"], errors="coerce").dt.year.max()) if not df.empty else 2025
with st.sidebar:
    sel_regions, sel_status, (ymin, ymax), show_labels = View.sidebar_filters(regions, statuses, yr_min, yr_max)


# Filter + color + tooltip
fdf = svc.filter(df, sel_regions, sel_status, ymin, ymax)
fdf = svc.colorize(fdf)
fdf = svc.tooltipify(fdf)


# Map
map_token = get_mapbox_token(st.secrets)
mb = MapBuilder(mapbox_token=map_token)
df_map = mb.minimal_map_df(fdf)
view_state = mb.avg_view(df_map)


# Build deck
layers = mb.build_layers(df_map, show_labels=show_labels)
deck = mb.deck(df_map, view_state)
# Add thematic layers after deck creation (keeps base tiles first)
for lyr in layers:
    deck.layers.append(lyr)


st.pydeck_chart(deck, use_container_width=True)


# Table + download
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Cases")
    table_df = svc.table_display(fdf).sort_values(["region", "country", "name"]) if not fdf.empty else fdf
    View.table(table_df)


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


st.subheader("Sources for filtered cases")
View.sources_panel(fdf)


st.caption("Note: This app displays entries from your CSV and sources you provide. It is not a legal or scholarly determination.")