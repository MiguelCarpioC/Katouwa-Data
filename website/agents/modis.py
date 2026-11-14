"""Agent 2: NASA ORNL DAAC MOD13Q1 observations, original QA and traceable filters.

Uses the documented public ORNL TESViS API. The /subset endpoint accepts at most
10 MODIS composite dates per request, but ORNL's gateway aborts requests that take
longer than ~60 s, so this client asks for a single pixel and few dates at a time.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
import logging
from pathlib import Path
import pandas as pd
from .common import APIError, CachedHTTP
from .planner import Site

log = logging.getLogger(__name__)
BASE = "https://modis.ornl.gov/rst/api/v1"
PRODUCT = "MOD13Q1"
BAND_MAP = {
    "250m_16_days_NDVI": "NDVI",
    "250m_16_days_EVI": "EVI",
    "250m_16_days_pixel_reliability": "PIXEL_RELIABILITY",
}


def modis_to_date(s: str) -> str:
    """A2025001 -> 2025-01-01."""
    return datetime.strptime(s, "A%Y%j").strftime("%Y-%m-%d")


def center_sample(raw: dict) -> list[dict]:
    """Extract a SINGLE center pixel with QA and preserve product version.

    A center pixel is not evidence of homogeneous mangrove land cover.
    """
    ncols, nrows = int(raw['ncols']), int(raw['nrows'])
    if ncols <= 0 or nrows <= 0:
        raise APIError("Bad MODIS spatial dimensions")
    idx = (nrows // 2) * ncols + (ncols // 2)
    grouped = defaultdict(dict)
    for band_entry in raw.get('subset', []):
        name = band_entry.get('band')
        if name not in BAND_MAP:
            continue
        values = band_entry['data']
        if len(values) != ncols * nrows:
            raise APIError(f"Unexpected pixels for {name}: {len(values)} vs {ncols*nrows}")
        date = band_entry['modis_date']
        grouped[date][BAND_MAP[name]] = values[idx]
        grouped[date]['product_version'] = band_entry.get('version','unknown')
        grouped[date]['tile'] = band_entry.get('title', '')
    out = []
    for datecode, item in sorted(grouped.items()):
        if not {'NDVI', 'EVI', 'PIXEL_RELIABILITY'} <= item.keys():
            raise APIError(f"Missing NDVI/EVI/QA for composite {datecode}: {sorted(item.keys())}")
        try:
            qa = int(item['PIXEL_RELIABILITY'])
        except (ValueError, TypeError):
            raise APIError(f"Non-numeric pixel reliability in {datecode}")
        for var in ("NDVI", "EVI"):
            try:
                raw_value = int(item[var])
            except (ValueError, TypeError):
                raw_value = -9999
            is_range_ok = -2000 <= raw_value <= 10000
            qc_status = "good" if qa == 0 else ("marginal" if qa == 1 else "bad_or_missing")
            out.append({
                "date": modis_to_date(datecode),
                "variable": var,
                "value": raw_value * 0.0001 if is_range_ok else None,
                "raw_value": raw_value,
                "qa": qa,
                "qc_status": qc_status,
                "is_qa_valid": bool(qa == 0 and is_range_ok),
                "source": "NASA ORNL DAAC TESViS",
                "product": PRODUCT,
                "product_version": item['product_version'],
                "unit": "dimensionless_index",
                "scale": "already_scaled",
                "spatial_sample": "single_center_MODIS_pixel",
                "tile": item['tile'],
                "modis_date": datecode,
            })
    return out


def unwrap_dates(payload: object) -> list[dict]:
    """Accept the documented ORNL object wrapper; reject server errors explicitly.

    NASA's /dates payload is normally {"dates": [...]}, not necessarily [...].
    Any unexpected response must fail closed: no invented observations.
    """
    if isinstance(payload, dict):
        if 'dates' in payload:
            dates = payload['dates']
        else:
            detail = payload.get('error') or payload.get('message') or payload.get('detail') or payload.get('status')
            raise APIError(f"NASA /dates did not contain a dates array. API detail: {str(detail or payload)[:350]}")
    elif isinstance(payload, list):
        dates = payload
    else:
        raise APIError(f"NASA /dates returned unsupported type: {type(payload).__name__}")
    if not isinstance(dates, list):
        raise APIError(f"NASA /dates field is not an array (received {type(dates).__name__})")
    if not dates:
        raise APIError("NASA /dates returned an empty dates array for these coordinates/product")
    malformed = [i for i, d in enumerate(dates) if not isinstance(d, dict) or not isinstance(d.get('modis_date'), str) or not __import__('re').fullmatch(r'A\d{7}', d['modis_date'])]
    if malformed:
        raise APIError(f"NASA /dates contained malformed composite entries at indices {malformed[:5]}")
    return dates


class SatelliteCollector:
    def __init__(self, client: CachedHTTP):
        self.client = client

    def collect(self, site: Site, start: int, end: int, chunksize: int = 2) -> pd.DataFrame:
        if not 1 <= chunksize <= 10:
            raise ValueError("The public ORNL subset endpoint allows max 10 composites per request")
        # NASA ORNL /dates currently returns {"dates": [{"modis_date": ...}, ...]}.
        # Older clients/fixtures can return the list directly. Support both.
        url = f"{BASE}/{PRODUCT}/dates"
        coords = {"latitude": site.latitude, "longitude": site.longitude}
        payload = self.client.get_json(url, coords)
        try:
            dates = unwrap_dates(payload)
        except APIError as exc:
            # Previously cached API error objects may be left by old versions of
            # CachedHTTP. Retry only those invalid objects, not real date lists.
            if isinstance(self.client, CachedHTTP) and not self.client.offline:
                log.warning("Invalid MODIS dates response at %s; refreshing endpoint cache once: %s", site.id, exc)
                payload = self.client.get_json(url, coords, refresh=True)
                dates = unwrap_dates(payload)
            else:
                raise
        available = sorted({x['modis_date'] for x in dates})
        selected = [d for d in available if start <= int(d[1:5]) <= end]
        if not selected:
            raise APIError(f"No MODIS composites in {start}-{end} for site {site.id}")
        rows = []
        self.failed_chunks: list[dict] = []
        for index in range(0, len(selected), chunksize):
            chunk = selected[index:index+chunksize]
            params = {
                "latitude": site.latitude,
                "longitude": site.longitude,
                "startDate": chunk[0],
                "endDate": chunk[-1],
                # Only the center pixel is analysed, so request just that pixel.
                "kmAboveBelow": 0,
                "kmLeftRight": 0,
            }
            try:
                raw = self.client.get_json(f"{BASE}/{PRODUCT}/subset", params)
                if not isinstance(raw, dict):
                    raise APIError("Unexpected MODIS subset response (expected object)")
                rows.extend(center_sample(raw))
            except APIError as exc:
                # Keep the composites that did download; record the gap explicitly.
                # Re-running resumes from the cache and retries only missing chunks.
                self.failed_chunks.append({"start": chunk[0], "end": chunk[-1], "error": str(exc)[:300]})
                log.error("%s: MODIS composites %s..%s not retrieved: %s", site.id, chunk[0], chunk[-1], exc)
                continue
            log.info("%s, dates %d/%d: extracted %d candidate band values", site.id, min(index+len(chunk),len(selected)), len(selected), len(rows))
        df = pd.DataFrame(rows)
        if df.empty:
            raise APIError(f"No MODIS values extracted at {site.id}; {len(self.failed_chunks)} requests failed. "
                           f"Last error: {self.failed_chunks[-1]['error'] if self.failed_chunks else 'n/a'}")
        df = df.drop_duplicates(['date', 'variable']).sort_values(['date','variable'])
        df['site'] = site.id
        df['latitude'] = site.latitude
        df['longitude'] = site.longitude
        df['site_warning'] = site.warning
        return df
