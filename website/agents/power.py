"""Agent 3: monthly NASA POWER modeled meteorological inputs."""
from __future__ import annotations
import pandas as pd
from .common import APIError, CachedHTTP
from .planner import Site

BASE = "https://power.larc.nasa.gov/api/temporal/monthly/point"
PARAMS = {"T2M", "PRECTOTCORR"}


class ClimateCollector:
    def __init__(self, client: CachedHTTP):
        self.client = client

    def collect(self, site: Site, start: int, end: int) -> pd.DataFrame:
        params = {
            "parameters": ",".join(sorted(PARAMS)),
            "community": "AG",
            "latitude": site.latitude,
            "longitude": site.longitude,
            "start": start,
            "end": end,
            "format": "JSON",
        }
        raw = self.client.get_json(BASE, params)
        if not isinstance(raw, dict):
            raise APIError("NASA POWER response should be JSON object")
        if raw.get('messages'):
            raise APIError(f"NASA POWER error or warning messages: {raw['messages']}")
        try:
            series = raw['properties']['parameter']
        except KeyError as exc:
            raise APIError(f"Unexpected NASA POWER JSON schema: {exc}") from exc
        data = []
        metadata = raw.get('parameters', {})
        for variable in sorted(PARAMS):
            if variable not in series:
                raise APIError(f"NASA POWER missing requested parameter: {variable}")
            for year_month, value in series[variable].items():
                if not (len(year_month) == 6 and year_month.isdigit() and 1 <= int(year_month[4:6]) <= 12):
                    continue
                value = pd.to_numeric(value, errors='coerce')
                if pd.isna(value) or value <= -999:
                    continue
                unit = metadata.get(variable,{}).get('units', "see NASA POWER metadata")
                data.append({
                    "date": f"{year_month[:4]}-{year_month[4:6]}-15",
                    "site": site.id,
                    "variable": variable,
                    "value": float(value),
                    "source": "NASA POWER",
                    "product": "POWER monthly meteorological time series",
                    "unit": unit,
                    "latitude": site.latitude,
                    "longitude": site.longitude,
                    "scale": "already_scaled",
                    "spatial_sample": "regional_model_grid_not_field_station",
                    "is_qa_valid": True,
                    "site_warning": site.warning,
                })
        result = pd.DataFrame(data)
        if result.empty:
            raise APIError("POWER supplied no valid monthly observations")
        return result.sort_values(['date','variable'])
