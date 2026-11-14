"""Offline agent contract tests. These fixtures are FAKE and never output as observations."""
import unittest
import pandas as pd
from pathlib import Path
import sys
import json
import tempfile
from unittest.mock import Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from agents.modis import modis_to_date, center_sample, SatelliteCollector, unwrap_dates
from agents.power import ClimateCollector
from agents.planner import Site, ResearchPlanner
from agents.quality import QualityStatisticsAgent
from agents.common import CachedHTTP, APIError

SITE=Site('TEST','Test only',10.71,-71.60,'test','UNVERIFIED')


def fake_modis(date):
    """Synthetic JSON schema fixture, used only in unit tests."""
    return {
      'nrows':3,'ncols':3,
      'subset':[
        {'band':'250m_16_days_NDVI','data':[1000]*4+[4500]+[1000]*4,'modis_date':date,'version':'061','title':'synthetic'},
        {'band':'250m_16_days_EVI','data':[1000]*4+[3300]+[1000]*4,'modis_date':date,'version':'061','title':'synthetic'},
        {'band':'250m_16_days_pixel_reliability','data':[0]*9,'modis_date':date,'version':'061','title':'synthetic'},
      ],
    }


class TestAgents(unittest.TestCase):
    def test_modis_date(self):
        self.assertEqual(modis_to_date('A2025001'),'2025-01-01')

    def test_center_pixel_scaling_qa(self):
        rows=center_sample(fake_modis('A2025001'))
        self.assertEqual(len(rows),2)
        ndvi=next(r for r in rows if r['variable']=='NDVI')
        self.assertAlmostEqual(ndvi['value'],0.45)
        self.assertTrue(ndvi['is_qa_valid'])
        self.assertEqual(ndvi['product_version'],'061')

    def test_qa_cloud_rejected(self):
        fixture=fake_modis('A2025001')
        fixture['subset'][2]['data'][4]=3
        rows=center_sample(fixture)
        self.assertTrue(all(not row['is_qa_valid'] for row in rows))

    def test_dates_composites_chunks(self):
        class FakeClient:
            def __init__(self): self.calls=[]
            def get_json(self,url,params):
                self.calls.append((url,params))
                if url.endswith('/dates'):
                    return [{'modis_date':f'A2025{d:03d}'} for d in [1,17,33,49,65,81,97,113,129,145,161]]
                first=int(params['startDate'][5:]); last=int(params['endDate'][5:]);
                d=[1,17,33,49,65,81,97,113,129,145,161]
                # Merge fake response to simulate multiple composites in one response.
                parts=[]
                for day in d:
                    if first<=day<=last:
                        parts += fake_modis(f'A2025{day:03d}')['subset']
                return {'nrows':3,'ncols':3,'subset':parts}
        cli=FakeClient()
        df=SatelliteCollector(cli).collect(SITE,2025,2025,chunksize=8)
        self.assertEqual(len(df),22)
        self.assertEqual(len(cli.calls),3)  # /dates + two chunks
        self.assertTrue(all((call[1]['startDate'] <= call[1]['endDate']) for call in cli.calls[1:]))
        cli=FakeClient()
        df=SatelliteCollector(cli).collect(SITE,2025,2025)  # default: 2 composites/request
        self.assertEqual(len(df),22)
        self.assertEqual(len(cli.calls),7)
        self.assertEqual(cli.calls[1][1]['kmAboveBelow'],0)

    def test_partial_modis_failure_keeps_good_chunks(self):
        class FlakyClient:
            def get_json(self,url,params):
                if url.endswith('/dates'):
                    return [{'modis_date':f'A2025{d:03d}'} for d in [1,17,33,49]]
                if params['startDate']=='A2025033':
                    raise APIError('502 Proxy Error')
                parts=[]
                for day in (int(params['startDate'][5:]),int(params['endDate'][5:])):
                    parts += fake_modis(f'A2025{day:03d}')['subset']
                return {'nrows':3,'ncols':3,'subset':parts}
        sat=SatelliteCollector(FlakyClient())
        df=sat.collect(SITE,2025,2025)
        self.assertEqual(sorted(df.modis_date.unique()),['A2025001','A2025017'])
        self.assertEqual(sat.failed_chunks[0]['start'],'A2025033')

    def test_documented_dates_object_wrapper(self):
        wrapped={'dates':[{'modis_date':'A2025001','calendar_date':'2025-01-01'}]}
        self.assertEqual(unwrap_dates(wrapped),wrapped['dates'])

    def test_dates_object_flow_with_existing_cache(self):
        class NASAResponseStub:
            def __init__(self): self.calls=[]
            def get_json(self, url, params):
                self.calls.append(url)
                if url.endswith('/dates'):
                    return {'dates':[{'modis_date':'A2025001','calendar_date':'2025-01-01'}]}
                return fake_modis('A2025001')
        client=NASAResponseStub()
        df=SatelliteCollector(client).collect(SITE,2025,2025)
        self.assertEqual(len(df),2)
        self.assertEqual(len(client.calls),2)

    def test_dates_api_error_is_not_treated_as_observations(self):
        with self.assertRaisesRegex(APIError,'temporarily unavailable'):
            unwrap_dates({'error':'temporarily unavailable'})
        with self.assertRaisesRegex(APIError,'malformed'):
            unwrap_dates({'dates':[{'calendar_date':'2025-01-01'}]})
        with self.assertRaisesRegex(APIError,'empty'):
            unwrap_dates({'dates':[]})

    def test_stale_error_cache_is_refreshed_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            client=CachedHTTP(Path(tmp))
            url='https://modis.ornl.gov/rst/api/v1/MOD13Q1/dates'
            coords={'latitude': SITE.latitude,'longitude': SITE.longitude}
            import requests,hashlib
            req=requests.Request('GET',url,params=coords).prepare()
            stale_path=Path(tmp)/(hashlib.sha256(req.url.encode()).hexdigest()+'.json')
            stale_path.write_text(json.dumps({'message':'temporary gateway failure'}))
            payload={'dates':[{'modis_date':'A2025001'}]}
            subset=fake_modis('A2025001')
            class Result:
                def __init__(self,content): self.content=content
                def raise_for_status(self): pass
                def json(self): return self.content
            def fake_get(url,params,timeout,verify=True):
                return Result(payload if url.endswith('/dates') else subset)
            client.session.get=fake_get
            df=SatelliteCollector(client).collect(SITE,2025,2025)
            self.assertEqual(len(df),2)
            self.assertEqual(json.loads(stale_path.read_text()),payload)

    def test_modis_host_uses_verified_extra_root(self):
        from agents.common import EXTRA_ROOT_FILE
        with tempfile.TemporaryDirectory() as tmp:
            client=CachedHTTP(Path(tmp)/'cache')
            self.assertIs(client._verify_for('https://power.larc.nasa.gov/api/x'),True)
            bundle=Path(client._verify_for('https://modis.ornl.gov/rst/api/v1/MOD13Q1/dates'))
            text=bundle.read_text()
            self.assertIn(EXTRA_ROOT_FILE.read_text().split('-----BEGIN')[1][:60],text)
            self.assertGreater(text.count('BEGIN CERTIFICATE'),1)

    def test_power_months(self):
        class FakeClient:
            def get_json(self,url,params):
                return {'properties':{'parameter':{
                    'T2M':{'202501':29.5,'202513':29.0},
                    'PRECTOTCORR':{'202501':1.2,'202502':-999}
                }}, 'parameters':{'T2M':{'units':'C'},'PRECTOTCORR':{'units':'mm/day'}}}
        df=ClimateCollector(FakeClient()).collect(SITE,2025,2025)
        self.assertEqual(len(df),2)
        self.assertEqual(set(df.variable),{'T2M','PRECTOTCORR'})

    def test_planner_source(self):
        plan=ResearchPlanner(ROOT/'config/sites.json').plan(2016,2025)
        self.assertEqual(len(plan['sites']),2)
        self.assertEqual(plan['spatial_warning'], 'USER_SELECTED_MANGROVE_POINTS_NOT_FIELD_VERIFIED')


    def test_exact_two_user_selected_mangrove_points(self):
        plan=ResearchPlanner(ROOT/'config/sites.json').plan(2018,2025)
        self.assertEqual([s.id for s in plan['sites']], ['MANGROVE_POINT_1','MANGROVE_POINT_2'])
        self.assertAlmostEqual(plan['sites'][0].latitude, 10.705247, places=6)
        self.assertAlmostEqual(plan['sites'][0].longitude, -71.587554, places=6)
        self.assertAlmostEqual(plan['sites'][1].latitude, 10.700986, places=6)
        self.assertAlmostEqual(plan['sites'][1].longitude, -71.581910, places=6)

    def test_statistical_agent_full_contract(self):
        rows=[]
        # FAKE numbers for tests only; no saved file is presented as NASA data.
        for year in range(2016,2025):
            for month in range(1,13):
                rows.append({'date':f'{year}-{month:02d}-15',
                             'site':'TEST', 'variable':'T2M',
                             'value':25.0 + (year-2016) * 0.1,
                             'is_qa_valid':True})
        valid,annual,result=QualityStatisticsAgent().assess(pd.DataFrame(rows))
        self.assertEqual(len(valid),108)
        self.assertEqual(len(annual),9)
        self.assertTrue(bool(result['summary'].iloc[0]['trend_valid']))
        self.assertAlmostEqual(result['summary'].iloc[0]['slope_per_year'],0.1,places=5)
        self.assertFalse(result['audit']['mangrove_cover_verified'])

    def test_no_automatic_fake_data_on_failed_api(self):
        with tempfile.TemporaryDirectory() as d:
            client=CachedHTTP(Path(d),offline=True)
            with self.assertRaises(APIError):
                client.get_json('https://example.com/real-only')

if __name__ == '__main__':unittest.main()
