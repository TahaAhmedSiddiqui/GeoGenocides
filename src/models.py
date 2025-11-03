from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Case:
    id: str
    name: str
    country: str
    region: str
    latitude: float
    longitude: float
    start_date: str
    status: str
    perpetrators: str
    targeted_group: str
    est_deaths: Optional[float]
    last_verified: str
    sources: str
    summary: str

    def tooltip_html(self) -> str:
        return (
            f"<b>{self.name}</b><br>"
            f"{self.country} — {self.region}<br>"
            f"Status: {self.status}<br>"
            f"Targeted: {self.targeted_group}<br>"
            f"Perpetrators: {self.perpetrators}<br>"
            f"Since: {self.start_date}<br>"
            f"Last verified: {self.last_verified}"
            )
