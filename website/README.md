# KATOUWA — Two Skies, One Territory

**NASA Space Apps Challenge 2026 | Earth System Trend Detective**  
**Status (14 Nov 2026): live NASA POWER retrieval verified (240 real monthly values, 2016–2025). The MODIS client is fixed (TLS root + resilient requests) but the ORNL server was returning 502/503 for every request during testing, so no MODIS values are included yet. Re-run when ORNL recovers.**

A five-stage pipeline (planner → NASA MODIS vegetation data → NASA POWER meteorology → QA/statistics → reporter) and a Streamlit explorer. This is a reproducible **working prototype**, not a demonstrated loss of mangrove cover. Only the two user-selected Capitán Chico mangrove locations P1/P2 are included; their MODIS pixel composition has not been independently field-verified.

## Quick start (Python 3.11+ recommended)

Two selected locations (WGS84, **six decimals**):

- P1 — 10.705247, -71.587554
- P2 — 10.700986, -71.581910

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Collect one REAL vegetation-index time series (Internet needed):
python run_agents.py --source modis --start 2016 --end 2025 --site MANGROVE_POINT_2
# Or collect REAL regional meteorology with fewer API requests:
python run_agents.py --source power --start 2014 --end 2025
streamlit run app.py
```

In the app, choose **Agent-verified NASA output** and click **Run NASA MODIS data agent**, or choose **NASA POWER live**. All API failures remain explicit. A deliberately labelled **SYNTHETIC interface test** is included for an internet-free visual rehearsal. Never use the synthetic mode in judging as NASA evidence.

## Getting MODIS data when ORNL is slow

- `modis.ornl.gov` chains to the public root *emSign Root CA - G1*, which current certifi/Mozilla bundles no longer include. `config/certs/emsign_root_ca_g1.pem` is trusted **only for that host**, and only if its SHA-256 fingerprint matches.
- ORNL's gateway cuts requests at ~60 s. The client requests only the center pixel and 2 composites per call, retries 5× with backoff, and **keeps successful chunks** when others fail (gaps are listed in `reports/run_manifest.json`).
- Responses are cached in `data/raw/cache/`, so simply re-run the same command to resume; only missing chunks are re-requested.
- Quick health check: `curl -s -o /dev/null -w "%{http_code}\n" https://modis.ornl.gov/rst/api/v1/products` (200 = up).

## Exactly what we measure

- `MOD13Q1` (NASA ORNL DAAC): center-pixel vegetation NDVI/EVI, approximately 250 m and 16-day composites. QA: `pixel_reliability == 0`, valid unscaled range, annual medians.
- `NASA POWER`: `T2M` (°C) and `PRECTOTCORR` (mm/day) monthly, gridded model/reanalysis. Annual means are descriptive, not evidence of mangrove loss.
- Annual exploratory Kendall p-value + Theil–Sen slope only when ≥10 valid dates per year and ≥6 eligible years. Residual serial correlation is not corrected.
- Existing thesis (Spelorzi, 2007) establishes historical community concern; it cannot be used as a quantitative modern ecological trend.
- We **do not** assert that NDVI proves mangrove loss, water toxicity, fisheries decline or cultural change. 30 m Landsat/HLS area analysis and community-led geolocation are next phases.

## Other NASA-provided routes

- [Giovanni](https://giovanni.gsfc.nasa.gov/): downloadable CSV time series for selected variables (typically coarse regional environmental indicators).
- [AppEEARS](https://appeears.earthdatacloud.nasa.gov/): point or polygon-based observations and QA; polygon products help validate the mangrove area, typically requiring a NASA Earthdata login.
- [Hydrology Time Series](https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series): hydrological model variables for context.
- [KNMI Climate Explorer](https://climexp.knmi.nl/): cross-check trends against climate datasets, taking account of dataset provenance.

Resources are not automatically interchangeable. An unused website link is not evidence that a dataset has been retrieved. For any external CSV use **Upload sourced CSV**, include `date,site,variable,value`, and independently check units, QA and dataset source.

## Provenance and limits

Original API JSON is SHA-256 traced in `data/raw/cache/`; the run result is `reports/run_manifest.json`. Processed observations, annual summaries and statistics are stored separately. If APIs fail: `NO_DATA_RETRIEVED` and no fake trend is generated.

## Offline QA

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
```

See `README_CN.md`, `PITCH_2MIN_EN.md`, `JUDGE_QA_EN.md`, and `AGENT_WORKPLAN.md`.
