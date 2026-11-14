"""Agent 1: area metadata, validated request configuration, and scope logging."""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Site:
    id: str
    name: str
    latitude: float
    longitude: float
    category: str
    warning: str


class ResearchPlanner:
    def __init__(self, sites_file: Path):
        self.sites_file = Path(sites_file)

    def plan(self, start: int, end: int, site_ids: list[str] | None = None) -> dict:
        if not (2000 <= start <= end <= 2025):
            raise ValueError("Use complete years from 2000 through 2025 (no incomplete 2026 data)")
        payload = json.loads(self.sites_file.read_text(encoding="utf-8"))
        all_sites = [Site(**s) for s in payload['sites']]
        sites = [s for s in all_sites if site_ids is None or s.id in site_ids]
        if not sites:
            raise ValueError("No sites matched selection")
        for site in sites:
            if not (-90 <= site.latitude <= 90 and -180 <= site.longitude <= 180):
                raise ValueError(f"Invalid coordinates: {site.id}")
        return {
            "sites": sites,
            "years": (start, end),
            "research_question": "Do vegetation and meteorological trends change over time near the Maracaibo coastal corridors?",
            "data_policy": "Observed satellite/model data only; report unverified land-cover identity explicitly",
            "spatial_warning": payload['site_status'],
            "source_notes": payload.get("source_notes", [])
        }
