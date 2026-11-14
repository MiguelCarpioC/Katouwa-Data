"""Download a REAL NASA POWER monthly time series over a point.
Requires Internet access. The coordinates identify an illustrative analysis
point, not a verified mangrove boundary or a field sampling station.
"""
import argparse
import pathlib
import requests
import pandas as pd

API = 'https://power.larc.nasa.gov/api/temporal/monthly/point'
VALID_PARAMS = {'T2M', 'PRECTOTCORR'}


def download(latitude: float, longitude: float, start: int, end: int,
             parameter: str = 'T2M', site: str = 'Pilot point') -> pd.DataFrame:
    if parameter not in VALID_PARAMS:
        raise ValueError(f"Parameter must be one of {sorted(VALID_PARAMS)}")
    params = dict(parameters=parameter, community='AG', longitude=longitude,
                  latitude=latitude, start=start, end=end, format='JSON')
    response = requests.get(API, params=params, timeout=90)
    response.raise_for_status()
    payload = response.json()
    if 'messages' in payload and payload['messages']:
        raise RuntimeError(f"NASA POWER returned warnings/errors: {payload['messages']}")
    values = payload['properties']['parameter'][parameter]
    rows = []
    for k, v in values.items():
        # Exclude yearly 'ANN' summaries if present; keep calendar months only.
        if len(k) != 6 or not k.isdigit():
            continue
        rows.append({'date': f'{k[:4]}-{k[4:]}-15', 'site':site,
                     'variable':parameter, 'value':v, 'latitude':latitude,
                     'longitude':longitude, 'source':'NASA POWER',
                     'unit':payload.get('parameters',{}).get(parameter,{}).get('units','see NASA POWER metadata')})
    out = pd.DataFrame(rows)
    if out.empty:
        raise RuntimeError('NASA POWER returned no monthly observations.')
    return out.sort_values('date')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--latitude',type=float,default=10.65)
    parser.add_argument('--longitude',type=float,default=-71.60)
    parser.add_argument('--start',type=int,default=2010)
    parser.add_argument('--end',type=int,default=2024)
    parser.add_argument('--parameter',choices=sorted(VALID_PARAMS),default='T2M')
    parser.add_argument('--site',default='Illustrative Maracaibo point')
    parser.add_argument('--output',default='data/nasa_power_t2m.csv')
    args = parser.parse_args()
    df = download(args.latitude,args.longitude,args.start,args.end,args.parameter,args.site)
    output = pathlib.Path(args.output)
    output.parent.mkdir(exist_ok=True,parents=True)
    df.to_csv(output,index=False)
    print(f'NASA POWER: downloaded {len(df)} monthly values → {output}')
