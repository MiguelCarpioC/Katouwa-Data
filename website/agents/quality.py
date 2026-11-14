"""Agent 4: quality gating and traceable trend computation."""
from __future__ import annotations
import pandas as pd
from analysis import annual_aggregate, trend


class QualityStatisticsAgent:
    def assess(self, raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
        if raw.empty:
            raise ValueError("Cannot assess empty data")
        valid = raw.loc[raw['is_qa_valid'].fillna(False)].copy()
        valid = valid.dropna(subset=['value'])
        if valid.empty:
            raise ValueError("All observations were rejected by quality screening")
        # Stronger annual sample threshold avoids claiming a full seasonal
        # annual value from just 1-2 observations.
        summaries = []
        stats = []
        for (site, variable), group in valid.groupby(['site','variable']):
            stat = 'median' if variable in ('NDVI','EVI') else 'mean'
            minimum = 10
            annual = annual_aggregate(group, statistic=stat)
            annual['site'] = site
            annual['variable'] = variable
            annual['aggregation'] = stat
            annual['enough_data'] = annual['count'] >= minimum
            summaries.append(annual)
            eligible = annual.loc[annual['enough_data']].copy()
            if eligible.empty:
                result = {'valid':False, 'reason':f'No years with ≥{minimum} observations'}
            else:
                result = trend(eligible)
            stats.append({
                'site': site,
                'variable':variable,
                'usable_observations': len(group),
                'total_raw_observations': int(len(raw[(raw.site==site)&(raw.variable==variable)])),
                'annual_complete_years': int(len(eligible)),
                'trend_valid':bool(result['valid']),
                'slope_per_year':result.get('slope'),
                'p_value':result.get('p'),
                'kendall_tau':result.get('tau'),
                'slope_lower_95':result.get('low'),
                'slope_upper_95':result.get('high'),
                'estimated_total_change':result.get('delta'),
                'significant_exploratory_p005':result.get('significant'),
                'warning': ('EXPLORATORY ONLY: unadjusted temporal autocorrelation/spatial multiple tests; '
                            'sampling points not validated mangrove pixels; model-gridded POWER data')
                            if result['valid'] else result.get('reason'),
            })
        year_df = pd.concat(summaries, ignore_index=True)
        stats_df = pd.DataFrame(stats)
        audit = {
            'total_input_rows':int(len(raw)),
            'accepted_rows':int(len(valid)),
            'rejected_rows':int(len(raw)-len(valid)),
            'mangrove_cover_verified':False,
            'spatial_extent_mapping_performed':False,
            'community_observations_included':False,
            'corrected_for_temporal_autocorrelation':False,
        }
        return valid, year_df, {'summary':stats_df,'audit':audit}
