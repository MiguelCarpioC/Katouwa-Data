# KATOUWA — autonomous agent delegation / current execution

**Objective:** demonstrate an inspectable Earth-system time-series tool and its community-grounded application, without overstating results.

| Agent | Responsibility | Definition of done | Status in this delivery |
|---|---|---|---|
| A0 / Orchestrator | Define evidence tiers and release gates | Reproducible pipeline, manifest, no silent substitutions | DONE (offline) |
| A1 / Satellite scientist | Query NASA ORNL MOD13Q1 NDVI/EVI; retain pixel QA | Center pixel time series and exact API trace | CODE READY; LIVE DOWNLOAD BLOCKED (DNS) |
| A2 / Climate scientist | Query NASA POWER T2M and PRECTOTCORR | Monthly meteorology, correct unit labels | CODE READY; LIVE DOWNLOAD BLOCKED (DNS) |
| A3 / Statistical auditor | Validate, annual summaries, Theil–Sen/Kendall | Explicit sample minima, no unsupported inference | CODE READY; OFFLINE TESTED |
| A4 / Community and ethics | Ground local narrative in thesis; gate consent | No invented quotes, consent-gated uploads | DONE (historical reference); voices not supplied |
| A5 / Product and storytelling | Streamlit map+charts, provenance notices, pitch | 2-min narrative, judge Q&A, demo fallback | DONE (static/code; live UI not visually verified) |

## Critical release gates

1. Do not describe exploratory pixels as mapped red mangrove stands.
2. Never use synthetic values in a scientific result slide.
3. Never conflate NASA POWER modeled temperature/rainfall with pollution measurements.
4. Report Kendall p-values as exploratory; note autocorrelation and multiple-comparison limitations.
5. Do not use community audio, photographs, words or names without informed consent.
6. Do not claim a working/field-tested Ñeruna floating island; concept only.
7. If no API retrieval succeeds, pitch the working *method and demonstrator*, clearly indicating that the NASA live analysis has not yet run.

## Demo sequence

- Run NASA POWER via app if available; show *what variable*, *where*, *how much*, *is it significant?*
- Select MODIS result if available; demonstrate QA and sample pixel caveat.
- Open Two skies: historical community field research and consent workflow.
- Show La Ñeruna as an experimental concept only.
- Open audit tab and show the source URLs and process manifest.

## Required inputs which this agent cannot independently supply

Team account submission on NASA platform; community-owned consented audio; authoritative field-verified mangrove boundary; a networked environment to make live NASA API calls. These are explicit dependencies, not blockers for the code package.
