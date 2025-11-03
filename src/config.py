from __future__ import annotations
import os
from pathlib import Path
from typing import List


REQUIRED_COLS: List[str] = [
    "id", "name", "country", "region", "latitude", "longitude",
    "start_date", "status", "perpetrators", "targeted_group",
    "est_deaths", "last_verified", "sources", "summary",
]


PREFERRED_PATH = Path("data/genocides.csv")
FALLBACK_PATH = Path("genocides.csv")


STATUS_COLOR = {
    "ongoing": [220, 20, 60], # crimson
    "escalating": [255, 140, 0], # dark orange
    "at-risk": [255, 215, 0], # gold
}
DEFAULT_COLOR = [100, 149, 237] # cornflower blue


def get_mapbox_token(streamlit_secrets) -> str:
    """Return Mapbox token from env or Streamlit secrets (if secrets file exists)."""
    token = os.getenv("MAPBOX_API_KEY", "")
    try:
        from pathlib import Path
        if Path.home().joinpath(".streamlit", "secrets.toml").exists() or Path(".streamlit/secrets.toml").exists():
            try:
                token = streamlit_secrets.get("MAPBOX_API_KEY", token) # type: ignore[attr-defined]
            except Exception:
                pass
    except Exception:
        pass
    return token