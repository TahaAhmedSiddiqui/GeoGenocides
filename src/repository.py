from __future__ import annotations
from pathlib import Path
from typing import Iterable, List
import pandas as pd


from .config import REQUIRED_COLS
from .models import Case


class CSVRepository:
    def __init__(self, preferred: Path, fallback: Path):
        self.preferred = preferred
        self.fallback = fallback

    def _path(self) -> Path | None:
        if self.preferred.exists():
            return self.preferred
        if self.fallback.exists():
            return self.fallback
        return None

    def load(self) -> pd.DataFrame | None:
        path = self._path()
        if path is None:
            return None
        df = pd.read_csv(path)
        df.columns = [c.strip().lower() for c in df.columns]
        return df

    @staticmethod
    def validate(df: pd.DataFrame) -> List[str]:
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        return missing

    @staticmethod
    def to_cases(df: pd.DataFrame) -> Iterable[Case]:
        for _, r in df.iterrows():
            yield Case(
                id=str(r.get("id", "")),
                name=str(r.get("name", "")),
                country=str(r.get("country", "")),
                region=str(r.get("region", "")),
                latitude=float(r.get("latitude", float("nan"))),
                longitude=float(r.get("longitude", float("nan"))),
                start_date=str(r.get("start_date", "")),
                status=str(r.get("status", "")),
                perpetrators=str(r.get("perpetrators", "")),
                targeted_group=str(r.get("targeted_group", "")),
                est_deaths=(
                float(r.get("est_deaths")) if str(r.get("est_deaths", "")).strip() != "" else None
                ),
                last_verified=str(r.get("last_verified", "")),
                sources=str(r.get("sources", "")),
                summary=str(r.get("summary", "")),
            )
