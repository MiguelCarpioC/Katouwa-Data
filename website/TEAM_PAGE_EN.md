# NASA Space Apps 2026 — Suggested team page

**Project title:** KATOUWA — Two Skies, One Territory

**Challenge:** Be an Earth System Trend Detective!

**Tagline:** Satellite evidence from above; community knowledge from within.

## Project summary (submission-ready)

Environmental changes cannot always be understood through a satellite pixel alone. KATOUWA is a reproducible Earth-system trend investigation prototype, anchored in two user-selected mangrove-area sampling points in Capitán Chico near Santa Rosa de Agua, Venezuela. Our Python pipeline can retrieve NASA ORNL DAAC MOD13Q1 NDVI/EVI vegetation-index composites and NASA POWER regional meteorological time series, preserve raw responses, filter observations using quality flags, and compute exploratory annual Theil–Sen slopes and Kendall trend tests. An interactive Streamlit interface enables users to compare sampling locations and understand which findings are statistically supported, which are uncertain, and which cannot be inferred from the data.

The project introduces a complementary second evidence stream: locally grounded and consent-based community knowledge. A 2007 study of households in Capitán Chico provides historical context; it is clearly distinguished from satellite evidence. Community contributions require consent and provenance, and are never treated as automatic proof of satellite interpretation. A future La Ñeruna biomimetic floating-island concept suggests how the research could eventually inspire field monitoring and ecological restoration experiments, subject to design, environmental and governance review.

KATOUWA answers the challenge questions: **What changed? Where? How much? Is the trend statistically significant?** It also adds a fifth question: **Whose knowledge helps interpret the change?**

**Release status (fill using real run manifest):** Implemented/tested offline; live NASA API retrieval still unverified in build environment. No measured mangrove-loss claim is made until valid satellite data and a verified mangrove boundary are available.

## Tools and data

- Python, pandas, SciPy, Plotly, Streamlit; JSON source manifest and checksums.
- NASA ORNL DAAC MOD13Q1: https://modis.ornl.gov/data/modis_webservice.html
- NASA POWER: https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
- AppEEARS (next step): https://appeears.earthdatacloud.nasa.gov/
- Giovanni (alternative export): https://giovanni.gsfc.nasa.gov/
- Historical grounding: Lissett Spelorzi (2007), Universidad Rafael Urdaneta, *Destrucción del Mangle y la Percepción de los Habitantes de Santa Rosa Sobre la Incidencia en su Calidad de Vida*.

**Do not list team members, assign licenses, or state live-result figures without verification.**
