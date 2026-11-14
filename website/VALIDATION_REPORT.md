# Build validation report — 2026-11-14

## Code coverage / static checks

- PASS: `python -m unittest discover -s tests -v` — **9 of 9** offline tests passed.
- PASS: `python -m compileall -q app.py agents run_agents.py fetch_power.py analysis.py` — Python syntax valid.
- PASS: config has exactly **two** sampling points: P1 (10.705247,-71.587554), P2 (10.700986,-71.581910); six-decimal coordinates retained.
- PASS: synthetic UI data is explicitly labelled `SYNTHETIC_DEMO_NOT_NASA` and isolated from official pipeline outputs.
- PASS: app provides a MODIS download trigger for both points, NASA POWER on-demand, a sourced CSV upload, and provenance/audit views.

## Connectivity gate

- BLOCKED: a real `NASA POWER` API attempt (2019–2025, P1) failed because the local execution environment could not resolve the NASA DNS hostname. Check `reports/run_manifest.json` for the exact error.
- NOT YET VERIFIED: real MODIS dates and subset requests on a network-enabled machine; actual NASA numeric results; full deployed Streamlit runtime visual verification (Streamlit not installed here).
- No claim of real greenness change, statistical significance, mangrove area reduction, marine pollution or community impact is made.

## Scientific / impact gates

- The historical 2007 university thesis is treated as source of its specific survey findings, not proof of 2026 loss.
- Geographic points P1/P2 were selected in the user's earlier project work. Satellite pixels are **not** validated as pure mangrove stands.
- MODIS NDVI/EVI are vegetation indicators; NASA POWER temperature/precipitation are coarse gridded meteorology.
- The proposed La Ñeruna floating island is not an implemented ecological solution.

## Re-run on networked Mac

```bash
bash START_KATOUWA_MAC.command
# In sidebar choose Both P1 + P2 and Run NASA MODIS data agent.
```

Do not describe any local test fixture as NASA evidence. After a successful run the manifest must show `SUCCESS` or `SUCCESS_WITH_WARNINGS` with nonempty `sources_trace`, and CSV values should be inspected before public pitch.
