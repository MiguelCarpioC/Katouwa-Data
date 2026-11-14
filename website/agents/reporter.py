"""Agent 5: honest scientific outputs. Produces charts only for real downloaded data."""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


class Reporter:
    def __init__(self, outdir: Path):
        self.outdir = Path(outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)

    def build(self, valid: pd.DataFrame, annual: pd.DataFrame, assessments: dict, manifest: dict) -> dict:
        summary = assessments['summary']
        plot_paths = []
        for (site, var), group in annual.groupby(['site','variable']):
            filtered = group.loc[group['enough_data']]
            if len(filtered) < 2:
                continue
            fig, ax = plt.subplots(figsize=(9, 4.3))
            ax.plot(filtered['year'], filtered['value'], marker='o')
            ax.set(title=f'{site} — {var} (observational/model data)',
                   xlabel='Year',ylabel=f'Annual {filtered.aggregation.iloc[0]}')
            ax.grid(alpha=0.25)
            fig.tight_layout()
            filename = f"{site}_{var}_annual.png"
            fig.savefig(self.outdir / filename, dpi=160)
            plt.close(fig)
            plot_paths.append(str(self.outdir / filename))
        report = {
            'execution_status':'DATA_RETRIEVED_AND_ANALYZED',
            'input_observations':int(assessments['audit']['total_input_rows']),
            'accepted_observations':int(assessments['audit']['accepted_rows']),
            'analyzed_site_variable_pairs':int(len(summary)),
            'figures':plot_paths,
            'critical_limitations':[
                'Exploratory coordinates are not field verified as mangrove pixels',
                'MODIS 250-m mixed land/water pixels cannot isolate small mangrove stands',
                'NASA POWER represents regional modeled meteorology, not field observations',
                'Exploratory Kendall p-values do not correct for serial/spatial dependence',
                'No causal inference, community-culture measurement or water-pollution conclusion',
                'No satellite raster trend map is generated: this is a point-comparison prototype',
            ],
            'manifest':manifest,
        }
        (self.outdir/'research_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        summary.to_csv(self.outdir/'trend_summary.csv',index=False)
        return report
