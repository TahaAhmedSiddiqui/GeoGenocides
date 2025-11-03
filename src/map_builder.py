from __future__ import annotations
import pydeck as pdk
import pandas as pd


class MapBuilder:
    def __init__(self, mapbox_token: str | None = None):
        self.mapbox_token = mapbox_token or ""

    def minimal_map_df(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = ["longitude", "latitude", "color", "tooltip", "name"]
        keep = [c for c in cols if c in df.columns]
        m = df[keep].copy()
        m["longitude"] = pd.to_numeric(m["longitude"], errors="coerce")
        m["latitude"] = pd.to_numeric(m["latitude"], errors="coerce")
        m = m.dropna(subset=["longitude", "latitude"]) # only valid points
        return m

    def build_layers(self, df_map: pd.DataFrame, show_labels: bool = False):
        layers = []
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=df_map,
                get_position="[longitude, latitude]",
                get_fill_color="color",
                get_radius=200000,
                pickable=True,
                auto_highlight=True,
                )
            )
        if show_labels and not df_map.empty:
            layers.append(
                pdk.Layer(
                    "TextLayer",
                    data=df_map,
                    get_position="[longitude, latitude]",
                    get_text="name",
                    get_size=16,
                    get_color=[0, 0, 0],
                    get_angle=0,
                    get_alignment_baseline="bottom",
                )
            )
        return layers

    def deck(self, df_map: pd.DataFrame, view_state: pdk.ViewState):
        base_layers = []
        if self.mapbox_token:
            pdk.settings.mapbox_api_key = self.mapbox_token
            map_style = "mapbox://styles/mapbox/light-v10"
        else:
            map_style = None
            base_layers.append(
                pdk.Layer(
                    "TileLayer",
                    data="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                    min_zoom=0,
                    max_zoom=19,
                    tile_size=256,
                    )
        )
        return pdk.Deck(
            map_style=map_style,
            initial_view_state=view_state,
            layers=base_layers, # start with base
            tooltip={"html": "{tooltip}", "style": {"backgroundColor": "white", "color": "black"}},
        )

    @staticmethod
    def avg_view(df: pd.DataFrame) -> pdk.ViewState:
        if df.empty:
            return pdk.ViewState(latitude=20.0, longitude=0.0, zoom=1.5, bearing=0, pitch=0)
        return pdk.ViewState(
            latitude=float(df["latitude"].astype(float).mean()),
            longitude=float(df["longitude"].astype(float).mean()),
            zoom=1.5,
            bearing=0,
            pitch=0,
        )
