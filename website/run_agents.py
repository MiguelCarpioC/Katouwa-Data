#!/usr/bin/env python3
"""Run autonomous, sequential data agents. No fabricated observations.

Requires Internet access; caches raw NASA JSON and records explicit failures.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sys
import pandas as pd
from agents.common import CachedHTTP
from agents.planner import ResearchPlanner
from agents.modis import SatelliteCollector
from agents.power import ClimateCollector
from agents.quality import QualityStatisticsAgent
from agents.reporter import Reporter

ROOT = Path(__file__).resolve().parent


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='KATOUWA 5-agent NASA real-data pipeline')
    parser.add_argument('--start',type=int,default=2016)
    parser.add_argument('--end',type=int,default=2025)
    parser.add_argument('--source',choices=['all','modis','power'],default='all')
    parser.add_argument('--site',action='append',help='site ID from config/sites.json; can repeat')
    parser.add_argument('--offline',action='store_true',help='only use cached JSON; never access Internet')
    parser.add_argument('--verbose',action='store_true')
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    manifest = {
        'started_utc':datetime.now(timezone.utc).isoformat(),
        'status':'STARTED',
        'collection_mode':'OFFLINE_CACHE' if args.offline else 'REAL_REMOTE_NASA_API',
        'sources_requested':args.source,
        'stages':[],
        'failures':[],
        'notes':['No dataset is substituted with synthetic data on download failure'],
    }
    report_dir = ROOT/'reports'
    report_dir.mkdir(parents=True,exist_ok=True)
    raw_dir = ROOT/'data'/'raw'
    raw_dir.mkdir(parents=True,exist_ok=True)
    processed_dir = ROOT/'data'/'processed'
    processed_dir.mkdir(parents=True,exist_ok=True)
    # Prevent stale output from a previous run being mistaken for current data.
    for artifact in (processed_dir/'real_nasa_observations.csv',
                     processed_dir/'annual_summaries.csv',
                     processed_dir/'quality_audit.json',
                     report_dir/'trend_summary.csv',
                     report_dir/'research_report.json'):
        artifact.unlink(missing_ok=True)
    for old_chart in report_dir.glob('*_annual.png'):
        old_chart.unlink()

    def save_manifest():
        (report_dir/'run_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False,default=str),encoding='utf-8')

    try:
        plan = ResearchPlanner(ROOT/'config'/'sites.json').plan(args.start,args.end,args.site)
    except Exception as exc:
        manifest['status']='PLAN_FAILED'
        manifest['failures'].append(str(exc))
        save_manifest()
        logging.error("Planning failed: %s",exc)
        return 2
    manifest['stages'].append({'name':'ResearchPlanner','status':'OK','site_count':len(plan['sites']),'years':list(plan['years'])})
    manifest['spatial_warning'] = plan['spatial_warning']
    client = CachedHTTP(raw_dir/'cache',offline=args.offline)
    frames=[]
    satellite = SatelliteCollector(client)
    climate = ClimateCollector(client)
    # POWER's coarse climate grid can cover all candidate points; retrieve only once
    # to avoid implying that adjacent points represent independent weather stations.
    power_site_id = plan['sites'][0].id
    for site in plan['sites']:
        if args.source in ('all','modis'):
            try:
                df = satellite.collect(site,args.start,args.end)
                df.to_csv(raw_dir/f'{site.id}_MODIS_OBSERVATIONS_WITH_QA.csv',index=False)
                frames.append(df)
                missing = satellite.failed_chunks
                manifest['stages'].append({'name':'SatelliteCollector','site':site.id,
                                           'status':'PARTIAL' if missing else 'OK',
                                           'rows':len(df),'good_rows':int(df.is_qa_valid.sum()),
                                           'missing_composite_ranges':missing})
                if missing:
                    manifest['failures'].append({'name':'SatelliteCollector','site':site.id,
                                                 'message':f'{len(missing)} MODIS requests failed; re-run to resume from cache',
                                                 'missing':[f"{m['start']}..{m['end']}" for m in missing]})
            except Exception as exc:
                manifest['failures'].append({'name':'SatelliteCollector','site':site.id,'message':str(exc)})
                logging.error('MODIS download failed at %s: %s',site.id,exc)
        if args.source in ('all','power') and site.id == power_site_id:
            try:
                df=climate.collect(site,args.start,args.end)
                df.to_csv(raw_dir/f'{site.id}_POWER_OBSERVATIONS.csv',index=False)
                frames.append(df)
                manifest['stages'].append({'name':'ClimateCollector','site':site.id,'status':'OK','rows':len(df)})
            except Exception as exc:
                manifest['failures'].append({'name':'ClimateCollector','site':site.id,'message':str(exc)})
                logging.error('POWER download failed at %s: %s',site.id,exc)
    manifest['sources_trace']=client.trace
    if not frames:
        manifest['status']='NO_DATA_RETRIEVED'
        save_manifest()
        logging.error('No real NASA data downloaded. Do not create trend claims.')
        return 3
    combined = pd.concat(frames,ignore_index=True)
    try:
        valid,annual,assessments=QualityStatisticsAgent().assess(combined)
    except Exception as exc:
        manifest['status']='QUALITY_ANALYSIS_FAILED'
        manifest['failures'].append({'name':'QualityStatisticsAgent','message':str(exc)})
        save_manifest()
        logging.error('Quality/stats stage failed: %s',exc)
        return 4
    valid.to_csv(processed_dir/'real_nasa_observations.csv',index=False)
    annual.to_csv(processed_dir/'annual_summaries.csv',index=False)
    (processed_dir/'quality_audit.json').write_text(json.dumps(assessments['audit'],ensure_ascii=False,indent=2),encoding='utf-8')
    manifest['stages'].append({'name':'QualityStatisticsAgent','status':'OK','good_rows':len(valid)})
    manifest['status']='SUCCESS_WITH_WARNINGS' if manifest['failures'] else 'SUCCESS'
    manifest['finished_utc']=datetime.now(timezone.utc).isoformat()
    Reporter(report_dir).build(valid,annual,assessments,manifest)
    manifest['stages'].append({'name':'Reporter','status':'OK'})
    save_manifest()
    logging.info('DONE: %d cleaned real NASA measurements; read reports/trend_summary.csv and data/processed/real_nasa_observations.csv',len(valid))
    return 0


if __name__=='__main__':
    sys.exit(main())
