# Jury questions — scientifically defensible answers

**Q: Where is your NASA data?**  
A: The app integrates two official NASA APIs: ORNL DAAC MOD13Q1 vegetation indices with quality flags, and POWER monthly meteorological time series. `run_manifest.json` records whether extraction actually succeeded and the exact URLs and SHA-256 hashes. We never substitute invented data if an API fails.

**Q: Why not Landsat 30 m?**  
A: MODIS 250 m is a quick working baseline but can mix water, houses and trees in Santa Rosa. A verified mangrove polygon and Landsat/HLS 30 m analysis are needed before area-loss claims. We explicitly label current pixels as candidates.

**Q: Can NDVI prove that mangroves have died?**  
A: No. It detects variations in greenness, potentially influenced by phenology, water, viewing geometry, pixel mixing and other factors. A spectral trend prompts investigation; it is not direct proof of cause, mortality or coverage loss.

**Q: What makes a trend significant?**  
A: The prototype calculates annual Theil–Sen slopes and Kendall p-values, only after quality screening and minimum sample requirements. This is exploratory significance because we have not corrected serial correlation or multiple tests.

**Q: Why did you not use Giovanni / AppEEARS / KNMI?**  
A: All are valid discovery and comparison channels. The MVP automates NASA ORNL and POWER public APIs and accepts sourced CSVs from those tools. AppEEARS can later process verified polygons and QA-aware higher-resolution products; KNMI can help check climate-trend robustness.

**Q: How do you integrate Indigenous knowledge ethically?**  
A: We cite a historic thesis separately and only include new recordings or testimony with informed community consent, proper attribution and community control. We do not claim AI “understands” a culture or turn oral history into a calibrated sensor.

**Q: Is La Ñeruna built and validated?**  
A: No. It is an experimental biomimetic design hypothesis. Engineering, ecology, permission, maintenance and hydrodynamic studies are still needed.

**Q: What's different from another environmental dashboard?**  
A: Its core distinction is an auditable, uncertainty-aware **dual evidence architecture**: remote measurements alongside appropriately attributed local observations, with a path to actionable place-specific field validation.

**Q: Can you quantify oil, toxicity or local fisheries with NASA POWER or MODIS NDVI?**  
A: No. These products do not directly measure those outcomes. Specific water-quality sensors, validated remote-sensing products and field sampling would be needed.
