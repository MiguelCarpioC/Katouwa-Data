"""Statistical analysis for the KATOUWA prototype.

Statistical significance here is exploratory and assumes independence of annual
aggregates. It is not proof of ecological cause or community impact.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.stats import kendalltau, theilslopes

REQUIRED = {'date', 'site', 'variable', 'value'}


def validate(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"CSV must include: {', '.join(sorted(missing))}")
    out = df.copy()
    out['date'] = pd.to_datetime(out['date'], errors='coerce')
    out['value'] = pd.to_numeric(out['value'], errors='coerce')
    out = out.dropna(subset=['date', 'value', 'site', 'variable'])
    # Missing sentinel used by NASA POWER. Also prevent impossible NDVI.
    out = out.loc[out['value'] != -999]
    for col in ('site', 'variable'):
        out[col] = out[col].astype(str)
    if out.empty:
        raise ValueError('No usable dated observations were found.')
    return out


def annual_aggregate(df: pd.DataFrame, statistic: str = 'median', months: list[int] | None = None) -> pd.DataFrame:
    d = validate(df)
    if months is not None:
        d = d.loc[d.date.dt.month.isin(months)]
    if d.empty:
        raise ValueError('No observations in the chosen months.')
    d = d.assign(year=d.date.dt.year)
    method = 'mean' if statistic == 'mean' else 'median'
    result = d.groupby('year', as_index=False).agg(value=('value',method), count=('value','size'))
    return result


def trend(annual: pd.DataFrame) -> dict:
    if len(annual) < 6:
        return {'valid': False, 'reason':'At least six annual observations are required for this exploratory test.'}
    x = annual['year'].to_numpy(dtype=float)
    y = annual['value'].to_numpy(dtype=float)
    if len(np.unique(x)) != len(x):
        return {'valid':False, 'reason':'Annual years must be unique.'}
    if np.all(y == y[0]):
        return {'valid':True, 'n':len(y), 'slope':0.0, 'low':0.0,'high':0.0,
                'p':1.0,'tau':0.0, 'significant':False, 'delta':0.0}
    slope, intercept, lo, hi = theilslopes(y, x, alpha=0.95)
    kt = kendalltau(x, y)
    return {'valid':True, 'n':len(y), 'slope':float(slope),
            'low':float(lo), 'high':float(hi), 'p':float(kt.pvalue),
            'tau':float(kt.statistic), 'significant': bool(kt.pvalue < 0.05),
            'delta': float(slope * (max(x)-min(x)))}
