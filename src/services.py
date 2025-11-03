from __future__ import annotations
from typing import Iterable, List, Tuple
import pandas as pd


from .models import Case
from .config import STATUS_COLOR, DEFAULT_COLOR


class CaseService:
    @staticmethod
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        def _coerce_date(s: pd.Series) -> pd.Series:
            return pd.to_datetime(s, errors="coerce").dt.date

        df = df.copy()
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
        df["est_deaths"] = pd.to_numeric(df["est_deaths"], errors="coerce")
        df["start_date"] = _coerce_date(df["start_date"]) # becomes date or NaN
        df["last_verified"] = _coerce_date(df["last_verified"]) # becomes date or NaN
        return df

    @staticmethod
    def quality_issues(df: pd.DataFrame) -> List[Tuple[int, str]]:
        problems: List[Tuple[int, str]] = []
        for idx, row in df.iterrows():
            msgs = []
            lat = row.get("latitude")
            lon = row.get("longitude")
            if pd.isna(lat) or pd.isna(lon):
                msgs.append("lat/lon missing or invalid")
            else:
                try:
                    if not (-90 <= float(lat) <= 90 and -180 <= float(lon) <= 180):
                        msgs.append("lat/lon out of range")
                except Exception:
                    msgs.append("lat/lon invalid type")
            if not str(row.get("sources", "")).strip():
                msgs.append("missing sources")
            if msgs:
                problems.append((idx, "; ".join(msgs)))
        return problems

    @staticmethod
    def filter(df: pd.DataFrame, regions: List[str], statuses: List[str], year_min: int, year_max: int) -> pd.DataFrame:
        fdf = df.copy()
        if regions:
            fdf = fdf[fdf["region"].astype(str).isin(regions)]
        if statuses:
            fdf = fdf[fdf["status"].astype(str).isin(statuses)]
        sd = pd.to_datetime(fdf["start_date"], errors="coerce")
        mask_year = (sd.dt.year >= year_min) & (sd.dt.year <= year_max)
        return fdf[mask_year]

    @staticmethod
    def colorize(df: pd.DataFrame) -> pd.DataFrame:
        fdf = df.copy()
        fdf["color"] = fdf["status"].astype(str).str.lower().map(lambda s: STATUS_COLOR.get(s, DEFAULT_COLOR))
        return fdf

    @staticmethod
    def tooltipify(df: pd.DataFrame) -> pd.DataFrame:
        fdf = df.copy()
        fdf["tooltip"] = (
            "<b>" + fdf["name"].astype(str) + "</b><br>" +
            fdf["country"].astype(str) + " — " + fdf["region"].astype(str) + "<br>" +
            "Status: " + fdf["status"].astype(str) + "<br>" +
            "Targeted: " + fdf["targeted_group"].astype(str) + "<br>" +
            "Perpetrators: " + fdf["perpetrators"].astype(str) + "<br>" +
            "Since: " + fdf["start_date"].astype(str) + "<br>" +
            "Last verified: " + fdf["last_verified"].astype(str)
        )
        return fdf

    @staticmethod
    def table_display(df: pd.DataFrame) -> pd.DataFrame:
        cols = [
            "id", "name", "country", "region", "status",
            "targeted_group", "perpetrators", "start_date", "last_verified", "est_deaths",
        ]
        have = [c for c in cols if c in df.columns]
        return df[have]